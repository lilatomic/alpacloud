"""Fetch metrics from Prometheus metrics endpoint."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, NoReturn

import requests

from alpacloud.promls.metrics import Metric


@dataclass
class FetcherURL:
	"""Fetch metrics from Prometheus metrics endpoint."""

	url: str

	def fetch(self):
		"""Fetch metrics from url"""
		return requests.get(self.url, timeout=10).text.split("\n")


class ParseError(Exception):
	"""Error parsing Prometheus metrics endpoint."""

	def __init__(self, value, line: str, cursor: int | None = None, line_number: int | None = None):
		self.line = line
		self.cursor = cursor
		self.line_number = line_number
		super().__init__(value)

	def __str__(self) -> str:
		msg = super().__str__()
		if self.line_number is not None:
			msg += f" line_number={self.line_number}"
		msg += f" line={self.line}"
		if self.cursor is not None:
			msg += f" cursor={self.cursor}"

		return msg


tok_whitespace = re.compile(r"\s+")
tok_name = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


class LineReader:
	"""Parse elements from a line of Prometheus metrics text."""

	def __init__(self, line: str, line_number: int | None = None):
		self.line = line
		self.cursor = 0
		self.line_number = line_number

	def err(self, msg: str) -> NoReturn:
		"""Raise an error with the current state"""
		raise ParseError(msg, self.line, self.cursor, self.line_number)

	def peek(self) -> str:
		"""Peek at the next character"""
		return self.line[self.cursor]

	def peek_for(self, char: str) -> bool:
		"""Peek to check for a specific character"""
		return self.peek() == char

	def consume_for(self, char: str) -> str:
		"""Consume a character if it matches, otherwise return empty string"""
		if self.peek_for(char):
			self.cursor += 1
			return char
		return ""

	def restore(self, cursor: int):
		"""Restore the cursor to a previous position"""
		self.cursor = cursor

	def consume_whitespace(self) -> bool:
		"""Consume whitespace and return True if there was any"""
		match = tok_whitespace.match(self.line, self.cursor)
		if match:
			self.cursor = match.end()
			return True
		return False

	def read_name(self) -> str | None:
		"""Read a name token from the input line"""
		match = tok_name.match(self.line, self.cursor)
		if match:
			self.cursor = match.end()
			return match.group()
		return None

	def read_escaped(self, until: str):
		"""Read an escaped string literal"""
		out = ""
		while self.line[self.cursor] != until:
			# there's an optimisation opportunity to add in slices until escaped char is reached
			if self.line[self.cursor] == "\\":
				char_at = self.line[(self.cursor + 1)]
				self.cursor += 2
				if char_at == "n":
					out += "\n"
				elif char_at == "\\":
					out += "\\"
				elif char_at == '"':
					out += '"'
				else:
					self.err(f"Invalid escape sequence \\{char_at}")
			else:
				out += self.line[self.cursor]
				self.cursor += 1

			if self.cursor >= len(self.line):
				self.err("Unterminated string literal")
		self.consume_for('"')
		return out

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
		"""Read the remaining characters on the line"""
		return self.line[self.cursor :]


class Parser:
	"""Extract meaningful lines from Prometheus metrics text."""

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
	def parse_all(cls, text: list[str]) -> tuple[list[Parser.DataLine | Parser.MetaLine | None], list[ParseError]]:
		"""Parse all lines from Prometheus metrics endpoint"""
		o = []
		errs = []
		for i, line in enumerate(text):
			if not line.strip():
				continue
			try:
				o.append(Parser(LineReader(line, i)).p_anyline())
			except ParseError as e:
				errs.append(e)

		return o, errs

	def p_anyline(self) -> Parser.DataLine | Parser.MetaLine | None:
		"""Parse any kind of line from Prometheus metrics endpoint. Returns None for blank lines."""
		if not self.r.line.strip():
			return None

		if self.r.peek_for("#"):
			return self.p_metaline()
		else:
			return self.p_dataline()

	def p_metaline(self) -> Parser.MetaLine:
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

	def p_dataline(self):
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
		"""Parse a label"""
		name = self.r.read_name()
		if not self.r.consume_for("="):
			self.r.err("Expected `=` after label name")
		if not self.r.consume_for('"'):
			self.r.err('Expected `"` after `=`')
		reader = self.r
		value = reader.read_escaped('"')
		return name, value


@dataclass
class Collector:
	"""Collect metric lines into Metrics"""

	lines: list[Parser.DataLine | Parser.MetaLine | None]
	combine_submetrics: bool = True

	@staticmethod
	def basename(name: str) -> tuple[str, str | None]:
		"""Extract the base name from a submetric. For example, a histogram my_metric has submetrics like my_metric_bucket, my_metric_sum, my_metric_count"""
		maybe_base = name.rsplit("_", 1)
		if len(maybe_base) == 2:
			base, terminal = maybe_base
			if terminal in {
				"bucket",
				"quantile",
				"sum",
				"count",
			}:
				return base, terminal
		return name, None

	def assemble(self):
		"""Assemble parsed lines into metrics"""
		# TODO: gather comments
		meta = defaultdict(list)
		for line in self.lines:
			if isinstance(line, Parser.MetaLine):
				meta[self.basename(line.name)[0]].append(line)

		data = defaultdict(list)
		for line in self.lines:
			if isinstance(line, Parser.DataLine):
				data[self.basename(line.name)[0]].append(line)

		metrics = []
		for k, vs in data.items():
			metrics.extend(self.build_metric(k, meta[k], vs))

		return metrics

	def build_metric(self, base_name, meta: list[Parser.MetaLine], data: list[Parser.DataLine]) -> list[Metric]:
		"""Collect lines into Metric objects"""

		help = ""
		type = ""
		for meta_line in meta:
			if meta_line.kind == Parser.MetaKind.HELP:
				help = meta_line.data
			elif meta_line.kind == Parser.MetaKind.TYPE:
				type = meta_line.data

		label_sets = []
		for line in data:
			_, terminal = Collector.basename(line.name)
			if (
				self.combine_submetrics
				and type
				in {
					"summary",
					"histogram",
				}
				and terminal
				in {
					"sum",
					"count",
				}
			):
				# sum and count have no labels, so there's no need to collect them
				continue

			label_sets.append(line.labels)

		if self.combine_submetrics and type in {
			"summary",
			"histogram",
		}:
			return [Metric(base_name, help, type, label_sets)]
		else:
			names = set()
			for line in data:
				names.add(line.name)
			metrics = []
			for name in names:
				metrics.append(Metric(name, help, type, label_sets))
			return metrics
