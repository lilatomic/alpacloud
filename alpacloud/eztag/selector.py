"""Selector items based on their tags. Useful for when tags are external to the data."""

from typing import Generic, TypeVar

from alpacloud.eztag.logic import Expr
from alpacloud.eztag.tag import TagSet

Data = TypeVar("Data")


class Selector(Generic[Data]):
	"""Select items based on their tags"""

	def __init__(self, items: list[tuple[TagSet, Data]]):
		self.items = items

	def select(self, expr: Expr) -> list[Data]:
		"""Select items based on a predicate"""
		return [e[1] for e in self.select_with_tags(expr)]

	def select_with_tags(self, expr: Expr) -> list[tuple[TagSet, Data]]:
		"""Select items based on a predicate, returning their tags as well"""
		return [e for e in self.items if expr.check(e[0])]
