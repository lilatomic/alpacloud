"""Expressions for tag filtering"""

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
	"""A condition that checks if a tag set satisfies a predicate"""

	f: Callable[[TagSet], bool]

	def check(self, tags: TagSet) -> bool:
		return self.f(tags)


@dataclass(frozen=True, slots=True)
class And_(Expr):
	"""AND of multiple conditions"""

	conds: list[Cond_]

	def check(self, tags: TagSet) -> bool:
		return all(cond.check(tags) for cond in self.conds)


@dataclass(frozen=True, slots=True)
class Or_(Expr):
	"""OR of multiple conditions"""

	conds: list[Cond_]

	def check(self, tags: TagSet) -> bool:
		return any(cond.check(tags) for cond in self.conds)


@dataclass(frozen=True, slots=True)
class Not_(Expr):
	"""Negation of a condition"""

	cond: Cond_

	def check(self, tags: TagSet) -> bool:
		return not self.cond.check(tags)


@dataclass(frozen=True, slots=True)
class TagHas(Expr):
	"""Check if a tag set has a given tag, with any value"""

	k: str

	def check(self, tags: TagSet) -> bool:
		return tags.has(self.k)


@dataclass(frozen=True, slots=True)
class TagMatch(Expr):
	"""Check if a tag set has a given tag with a specific value"""

	k: str
	v: str | None

	def check(self, tags: TagSet) -> bool:
		return tags.match(self.k, self.v)


@dataclass(frozen=True, slots=True)
class TagRematch(Expr):
	"""Check if a tag set has a given tag with value matching a regular expression"""

	k: str
	v: str

	def check(self, tags: TagSet) -> bool:
		return tags.rematch(self.k, self.v)


@dataclass(frozen=True, slots=True)
class TagContains(Expr):
	"""Check if a tag set has a given tag with a specific value"""

	k: str
	v: str

	def check(self, tags: TagSet) -> bool:
		return tags.contains(self.k, self.v)
