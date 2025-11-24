from __future__ import annotations

import re
from dataclasses import dataclass

from alpacloud.eztag.multidict import MultiDict, V, K


@dataclass
class TagSet:
	"""A set of tags"""

	ts: MultiDict

	@classmethod
	def from_dict(cls, d: dict[K, V]) -> TagSet:
		return cls(MultiDict.from_dict(d))

	@classmethod
	def create(cls, d: dict[K, V | list[V]]) -> TagSet:
		return cls(MultiDict.create(d))

	def has(self, k: str) -> bool:
		"""Check if the key exists in the tagset"""
		return k in self.ts

	def match(self, k: str, v: str | None) -> bool:
		"""Exact match the value for this key (returns True if any value matches)"""
		if not self.has(k):
			return False
		return v in self.ts[k]

	def rematch(self, k: str, v: str | re.Pattern) -> bool:
		"""Regex match the value for this key (returns True if any value matches)"""
		if isinstance(v, str):
			v = re.compile(v)

		if not self.has(k):
			return False

		return any(val is not None and v.fullmatch(val) is not None for val in self.ts[k])

	def contains(self, k: str, v: str) -> bool:
		"""Check if any value for this key contains the substring"""
		if not self.has(k):
			return False

		return any(val is not None and v in val for val in self.ts[k])
