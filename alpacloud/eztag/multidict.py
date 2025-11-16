from __future__ import annotations

from typing import Iterable, TypeAlias, TypeGuard

K: TypeAlias = str
V: TypeAlias = str | None


def _is_collection(obj) -> TypeGuard[Iterable]:
	"""
	Checks if an object is an iterable collection, excluding strings and bytes.
	"""
	return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes, bytearray))


class MultiDict:
	"""
	A dictionary that allows multiple values for the same key.
	This allows us to have a tag set like `env=prd, env=stg`
	"""

	def __init__(self):
		self.d: dict[K, set[V]] = {}

	@classmethod
	def from_dict(cls, d: dict[K, V]) -> MultiDict:
		md = cls()
		for k, v in d.items():
			md[k] = {v}
		return md

	@classmethod
	def create(cls, d: dict[K, Iterable[V] | V]) -> MultiDict:
		md = cls()
		for k, vs in d.items():
			n: set[V]
			if not _is_collection(vs):
				n = {vs}  # type: ignore # idk typeguard
			else:
				n = set(vs)
			md.d[k] = n
		return md

	def __getitem__(self, key) -> set[V]:
		return self.d[key]

	def __setitem__(self, key, value):
		self.d.setdefault(key, set()).add(value)

	def __contains__(self, key) -> bool:
		return key in self.d
