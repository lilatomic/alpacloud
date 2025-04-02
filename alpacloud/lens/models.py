from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar

K = TypeVar("K")
O = TypeVar("O")
T = TypeVar("T")


class ALens(Generic[O, T]):
	def get(self, o: O):
		"""Get the value"""

	def set(self, o: O, t: T):
		"""Set the value"""

	def bind(self, o: O) -> BoundLens[O, T]:
		"""Bind this lens to an object"""
		return BoundLens(o, self)

	def compose(self, l: ALens[O, T]):
		"""Apply this lens and another lens"""
		return ComposedLen(self, l)

	def __getitem__(self, k: K) -> ALens[O, T]:
		return LensGetitem(k)


class BoundLens(Generic[O, T]):
	def __init__(self, o: O, l: ALens[O, T]):
		self._o = o
		self._l = l

	def g(self) -> T:
		"""Get the value"""
		return self._l.get(self._o)

	def s(self, t: T) -> None:
		"""Set the value"""
		self._l.set(self._o, t)

	def m(self, f: Callable[[T], T]) -> None:
		"""Map the value"""
		self._l.set(self._o, f(self._l.get(self._o)))


@dataclass(frozen=True)
class ComposedLen(ALens[O, T]):
	l0: ALens[O, T]
	l1: ALens[O, T]

	def get(self, o: O):
		return self.l1.get(self.l0.get(o))

	def set(self, o: O, t: T):
		v0 = self.l0.get(o)
		self.l1.set(v0, t)
		self.l0.set(o, v0)


@dataclass(frozen=True)
class LensAttr(ALens[O, T]):
	attr: str

	def get(self, o: O) -> T:
		return getattr(o, self.attr)

	def set(self, o: O, t: T) -> None:
		setattr(o, self.attr, t)


@dataclass(frozen=True)
class LensGetitem(ALens[O, T]):
	key: str
	default: Optional[T] = None

	def get(self, o: O) -> T:
		if self.default is not None:
			try:
				return o.__getitem__(self.key)
			except KeyError:
				return self.default
		else:
			return o.__getitem__(self.key)

	def set(self, o: O, t: T) -> None:
		return o.__setitem__(self.key, t)
