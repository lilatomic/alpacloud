from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml


@dataclass
class Case:
	a: Any
	b: Any

	def __call__(self, f: Callable):
		assert f(self.a) == self.b


@dataclass
class ResourceLoader:
	base_path: Path

	def load_obj(self, name: str):
		return self._load_file(self.base_path / name)

	def _load_file(self, p: Path):
		return yaml.safe_load(p.open())

	def load_case(self, path, name: str):
		def l(e):
			return self._load_file(self.base_path / path / f"{name}.{e}.yml")

		return Case(l("a"), l("b"))

	def __getitem__(self, item):
		return self.load_obj(item + ".yml")


@dataclass
class StrStartsWith:
	tgt: str
	s: str

	def check(self) -> bool:
		status = self.s.startswith(self.tgt)
		if not status:
			print(f"{self.tgt} is not {self.s}")

		return status
