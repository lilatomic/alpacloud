from __future__ import annotations

import re
from dataclasses import dataclass

@dataclass
class TagSet:
	"""A set of tags"""
	ts: dict[str, str | None]

	def has(self, k: str) -> bool:
		"""Check if the key exists in the tagset"""
		return k in self.ts

	def match(self, k: str, v: str) -> bool:
		"""Exact match the value for this key"""
		return self.ts[k] == v

	def rematch(self, k: str, v: str | re.Pattern) -> bool:
		"""Regex match the value for this key"""
		if isinstance(v, str):
			v = re.compile(v)

		return self.has(k) and v.fullmatch(self.ts[k]) is not None

	def contains(self, k: str, v: str) -> bool:
		"""Check if the value for this key contains the substring"""
		return self.has(k) and self.ts[k] is not None and v in self.ts[k]
