"""Fetch metrics from Prometheus metrics endpoint."""

from __future__ import annotations

import re
from abc import ABC
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any

import requests

from alpacloud.promls.metrics import Metric


class Fetcher(ABC):
	""""""


@dataclass
class FetcherURL:
	"""Fetch metrics from Prometheus metrics endpoint."""

	url: str

	def fetch(self):
		return requests.get(self.url).text.split("\n")


class ParseError(Exception):
	def __init__(self, value, line: str):
		self.line = line
		super().__init__(value)

	def __str__(self) -> str:
		return super().__str__() + f" line={self.line}"


class Parser:
	"""Parse metrics from Prometheus metrics endpoint."""

	class State(Enum):
		metadata = "metadata"
		data = "data"

	@dataclass
	class DataLine:
		"""Data line from Prometheus metrics endpoint."""

		name: str
		labels: dict[str, str]
		value: Any
		timestamp: int | None = None

	class MetaKind(Enum):
		HELP = "HELP"
		TYPE = "TYPE"
		COMMENT = "COMMENT"

	@dataclass
	class MetaLine:
		"""Metadata line from Prometheus metrics endpoint."""

		name: str
		kind: Parser.MetaKind
		data: str

	def parse(self, lines: list[str]) -> dict[str, Metric]:
		"""Parse metrics from Prometheus metrics endpoint."""
		name2data = self.group_lines(lines)
		return {k: self.parse_metric(k, v) for k, v in name2data.items()}

	def group_lines(self, lines: list[str]):
		name2data = defaultdict(list)
		for line in lines:
			# escape empty lines
			if not line.strip():
				continue

			is_data = not line.startswith("#")

			if is_data:
				d = self.parse_data_line(line)
			else:
				d = self.parse_meta_line(line)

			name2data[d.name].append(d)
		return name2data

	@staticmethod
	def parse_data_line(line: str) -> DataLine:
		# TODO: handle escaping in lines
		x = line.split(" ", 1)
		if len(x) != 2:
			raise ParseError("Could not identify name in line", line)

		name_and_labels, data = x
		data = data.strip()

		if line.count("{") != line.count("}"):
			raise ParseError(r"Invalid data line, unmatched `{}` pair")

		pieces = list(filter(None, re.split(r"[{}]", name_and_labels)))
		if len(pieces) > 2:
			# TODO: better error
			raise ParseError(f"Invalid data line, split into incorrect number of pieces pieces: {len(pieces)}")

		name = pieces[0].strip()

		labels = {}
		if len(pieces) > 1:
			for label_pair in pieces[1].split(","):
				label_key, label_value = label_pair.split("=")
				labels[label_key.strip()] = label_value.strip('"')

		if " " in data:
			# if it's a counter, it will also contain a timestamp
			value, timestamp = data.split(" ", 1)
			timestamp = int(timestamp.strip())
		else:
			value, timestamp = data, None

		return Parser.DataLine(name, labels, value.strip(), timestamp)

	@staticmethod
	def parse_meta_line(line: str) -> MetaLine:
		if not line.startswith("#"):
			raise ParseError(r"Invalid metadata line, did not start with #")

		line = line.strip("#").strip()
		maybe_kind = line.split(" ", maxsplit=1)
		if maybe_kind[0] in Parser.MetaKind.__members__:
			kind = Parser.MetaKind(maybe_kind[0])
			tail = maybe_kind[1]
		else:
			kind = Parser.MetaKind.COMMENT
			tail = line

		if kind == Parser.MetaKind.COMMENT:
			return Parser.MetaLine("COMMENT", kind, tail)  # TODO: model comment so we don't have an arbitrary value for `name`
		[name, data] = tail.split(" ", maxsplit=1)

		return Parser.MetaLine(name, kind, data)

	@staticmethod
	def parse_metric(name, statements: list[Parser.DataLine | Parser.MetaLine]) -> Metric:
		# TODO: label sets
		# TODO: sample values

		help = ""
		type = ""
		for line in statements:
			if isinstance(line, Parser.MetaLine):
				if line.kind == Parser.MetaKind.HELP:
					help = line.data
				elif line.kind == Parser.MetaKind.TYPE:
					type = line.data

		return Metric(name, help, type)
