from abc import ABC
from dataclasses import dataclass
from typing import Callable

from alpacloud.eztag.tag import TagSet


class Expr(ABC):
	"""A predicate"""

	def check(self, tags: TagSet) -> bool:
		"""Check if the condition is satisfied"""
		raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Cond_(Expr):
	f: Callable[[TagSet], bool]

	def check(self, tags: TagSet) -> bool:
		return self.f(tags)


@dataclass(frozen=True, slots=True)
class And_(Expr):
	conds: list[Cond_]

	def check(self, tags: TagSet) -> bool:
		return all(cond.check(tags) for cond in self.conds)


@dataclass(frozen=True, slots=True)
class Or_(Expr):
	conds: list[Cond_]

	def check(self, tags: TagSet) -> bool:
		return any(cond.check(tags) for cond in self.conds)


@dataclass(frozen=True, slots=True)
class Not_(Expr):
	cond: Cond_

	def check(self, tags: TagSet) -> bool:
		return not self.cond.check(tags)


@dataclass(frozen=True, slots=True)
class TagHas(Expr):
	k: str

	def check(self, tags: TagSet) -> bool:
		return tags.has(self.k)


@dataclass(frozen=True, slots=True)
class TagMatch(Expr):
	k: str
	v: str | None

	def check(self, tags: TagSet) -> bool:
		return tags.match(self.k, self.v)


@dataclass(frozen=True, slots=True)
class TagRematch(Expr):
	k: str
	v: str

	def check(self, tags: TagSet) -> bool:
		return tags.rematch(self.k, self.v)


@dataclass(frozen=True, slots=True)
class TagContains(Expr):
	k: str
	v: str

	def check(self, tags: TagSet) -> bool:
		return tags.contains(self.k, self.v)
