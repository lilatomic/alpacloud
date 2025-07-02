"""Test helpers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml


@dataclass
class Case:
	"""A testcase for recorded tests"""

	a: Any
	b: Any

	def __call__(self, f: Callable):
		assert f(self.a) == self.b


@dataclass
class ResourceLoader:
	"""Load test resources"""

	base_path: Path

	def load_obj(self, name: str):
		"""Load a test resource"""
		return self._load_file((self.base_path / name).with_suffix(".yml"))

	def _load_file(self, p: Path):
		return yaml.safe_load(p.open())

	def load_case(self, path, name: str):
		"""Load a test case"""

		def _load_case_item(e):
			return self._load_file(self.base_path / path / f"{name}.{e}.yml")

		return Case(_load_case_item("a"), _load_case_item("b"))

	def __getitem__(self, item):
		return self.load_obj(item)


@dataclass
class StrStartsWith:
	"""Test whether a string starts with a prefix"""

	tgt: str
	s: str

	def check(self) -> bool:
		"""Run the check"""
		status = self.s.startswith(self.tgt)
		if not status:
			print(f"{self.tgt} is not {self.s}")

		return status
