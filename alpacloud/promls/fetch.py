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
	"""Error parsing Prometheus metrics endpoint."""

	def __init__(self, value, line: str, cursor: int | None = None):
		self.line = line
		self.cursor = cursor
		super().__init__(value)

	def __str__(self) -> str:
		msg = super().__str__() + f" line={self.line}"
		if self.cursor is not None:
			msg += f" cursor={self.cursor}"
		return msg


whitespace = re.compile(r"\s+")
name = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


class LineReader:
	def __init__(self, line: str):
		self.line = line
		self.cursor = 0

	def err(self, msg: str) -> None:
		raise ParseError(msg, self.line, self.cursor)

	def peek(self):
		return self.line[self.cursor]

	def peek_for(self, char: str) -> bool:
		return self.peek() == char

	def consume_for(self, char: str) -> str:
		if self.peek_for(char):
			self.cursor += 1
			return char
		return ""

	def restore(self, cursor: int):
		self.cursor = cursor

	def consume_whitespace(self) -> bool:
		match = whitespace.match(self.line, self.cursor)
		if match:
			self.cursor = match.end()
			return True
		return False

	def read_name(self):
		match = name.match(self.line, self.cursor)
		if match:
			self.cursor = match.end()
			return match.group()
		return None

	def read_escaped(self, until: str):
		out = ""
		while self.line[self.cursor] != until:
			# TODO: can optimise to add in slices until escaped char is reached
			if self.line[self.cursor] == "\\":
				# TODO: ensure valid escape sequences
				char_at = self.cursor + 1
				self.cursor += 2
				out += self.line[char_at]
			else:
				char_at = self.cursor
				self.cursor += 1
				out += self.line[char_at]

			if self.cursor >= len(self.line):
				self.err("Unterminated string literal")
		self.cursor += 1  # TODO: use consume_for?
		return out

	def read_label_value(self):
		return self.read_escaped('"')

	def read_value(self):
		"""Read a value from the line. Value must be a valid float, or NaN or Inf."""
		start = self.cursor
		end = start
		while len(self.line) > self.cursor and self.line[self.cursor] != " ":
			self.cursor += 1
			end = self.cursor
		try:
			return float(self.line[start:end])
		except ValueError:
			self.err("Invalid numeric value")

	def read_remaining(self):
		return self.line[self.cursor :]


class Parser:
	@dataclass
	class DataLine:
		"""Data line from Prometheus metrics endpoint."""

		name: str
		labels: dict[str, str]
		value: Any
		timestamp: int | None = None

	class MetaKind(Enum):
		"""Kind of the line of metadata."""

		HELP = "HELP"
		TYPE = "TYPE"
		COMMENT = "COMMENT"

	@dataclass
	class MetaLine:
		"""Metadata line from Prometheus metrics endpoint."""

		name: str
		kind: Parser.MetaKind
		data: str

	def __init__(self, r: LineReader):
		self.r = r

	@classmethod
	def parse_all(cls, text: str) -> list[Metric]:
		r = [Parser(LineReader(l)).p_anyline() for l in text.split("\n")]
		r = list(filter(None, r))
		r = Parser.assemble(r)
		return r

	@staticmethod
	def assemble(lines: list[Parser.DataLine | Parser.MetaLine]):
		"""Assemble parsed lines into metrics"""
		# TODO: gather comments
		meta = defaultdict(list)
		for line in lines:
			if isinstance(line, Parser.MetaLine):
				meta[line.name].append(line)

		metrics = []
		for line in lines:
			if isinstance(line, Parser.DataLine):
				metrics.append(Parser.parse_metric(line.name, meta[line.name], line))

		return metrics

	def p_anyline(self) -> Parser.DataLine | Parser.MetaLine | None:
		if not self.r.line.strip():
			return None

		if self.r.peek_for("#"):
			return self.p_comment()
		else:
			return self.p_metric()

	def p_comment(self):
		"""Parse a comment line"""
		self.r.consume_for("#")
		self.r.consume_whitespace()
		restore_cursor = self.r.cursor
		kind = self.r.read_name()
		if kind == "HELP" or kind == "TYPE":
			if not self.r.consume_whitespace():
				self.r.err(f"Expected whitespace after comment type {kind}")
			metric_name = self.r.read_name()
			if metric_name is None:
				self.r.err(f"Invalid metric name in {kind} comment")
			self.r.consume_whitespace()
			return Parser.MetaLine(metric_name, Parser.MetaKind(kind), self.r.read_remaining())
		else:
			self.r.restore(restore_cursor)
			return Parser.MetaLine("COMMENT", Parser.MetaKind.COMMENT, self.r.read_remaining())  # TODO: model comment so we don't have an arbitrary value for `name`

	def p_metric(self):
		"""Parse a metric line"""
		name = self.r.read_name()
		if name is None:
			self.r.err("Invalid metric name")

		labels = {}
		if self.r.consume_for("{"):
			label_name, label_value = self.p_label()
			labels[label_name] = label_value

			# consume all labels
			while self.r.consume_for(","):
				if self.r.peek_for("}"):  # We peek here because of potential trailing comma
					break
				label_name, label_value = self.p_label()
				labels[label_name] = label_value

			if not self.r.consume_for("}"):
				self.r.err("Expected closing brace after labels")

		if not self.r.consume_whitespace():
			self.r.err("Expected whitespace after labels")
		value = self.r.read_value()

		if self.r.consume_whitespace():
			timestamp = self.r.read_value()
		else:
			timestamp = None

		return Parser.DataLine(name, labels, value, timestamp)

	def p_label(self):
		name = self.r.read_name()
		if not self.r.consume_for("="):
			self.r.err("Expected `=` after label name")
		if not self.r.consume_for('"'):
			self.r.err('Expected `"` after `=`')
		value = self.r.read_label_value()
		return name, value

	@staticmethod
	def parse_metric(name, meta: list[Parser.MetaLine], data: Parser.DataLine) -> Metric:
		"""Subpaarser for an actual metric."""
		# TODO: label sets
		# TODO: sample values

		help = ""
		type = ""
		for line in meta:
			if line.kind == Parser.MetaKind.HELP:
				help = line.data
			elif line.kind == Parser.MetaKind.TYPE:
				type = line.data

		return Metric(name, help, type)
