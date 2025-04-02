from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Optional

O = TypeVar("O")
T = TypeVar("T")


class ALens(Generic[O, T]):
	def get(self, o: O): ...

	def set(self, o: O, t: T): ...

	def bind(self, o: O) -> BoundLens[O, T]:
		return BoundLens(o, self)


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
