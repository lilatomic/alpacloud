from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, ClassVar, Generic, Optional, TypeVar, Sequence, Type

K = TypeVar("K")
O = TypeVar("O")
T = TypeVar("T")
U = TypeVar("U")


class LensError(Exception):
	def __init__(self, message: str, lens: ALens):
		super().__init__(message)
		self.lens = lens


class ALens(Generic[O, T]):
	_has_path: ClassVar[bool] = False

	@abstractmethod
	def _get(self, o: O):
		"""Get the value"""

	@abstractmethod
	def _set(self, o: O, t: T):
		"""Set the value"""

	def _bind(self, o: O) -> BoundLens[O, T]:
		"""Bind this lens to an object"""
		return BoundLens(o, self)

	def _compose(self, l: ALens[O, T]):
		"""Apply this lens and another lens"""
		return LensComposed(self, l)

	def _path(self) -> str:
		return repr(self)

	def __getitem__(self, k: K) -> ALens[O, T]:
		return self._compose(LensGetitem(k))

	def __getattr__(self, item):
		return self._compose(LensAttr(item))

	def __mul__(self, other: O):
		return LensComposed(self, other)

	def __matmul__(self, other: O):
		return self._bind(other)


class Lens(ALens[O, T]):
	"""A lens to start"""

	def _get(self, o: O):
		return o

	def _set(self, o: O, t: T):
		return t

	def __repr__(self) -> str:
		return "Lens()"


class BoundLens(Generic[O, T]):
	def __init__(self, o: O, l: ALens[O, T]):
		self._o = o
		self._l = l

	def g(self) -> T:
		"""Get the value"""
		return self._l._get(self._o)

	def s(self, t: T) -> None:
		"""Set the value"""
		self._l._set(self._o, t)

	def m(self, f: Callable[[T], T]) -> None:
		"""Map the value"""
		self._l._set(self._o, f(self._l._get(self._o)))


@dataclass(frozen=True)
class LensComposed(ALens[O, T]):
	l0: ALens[O, T]
	l1: ALens[O, T]

	def _get(self, o: O):
		return self.l1._get(self.l0._get(o))

	def _set(self, o: O, t: T):
		v0 = self.l0._get(o)
		self.l1._set(v0, t)
		self.l0._set(o, v0)

	def _path(self) -> str:
		o = self.l0._path()

		if self.l1._has_path:
			o += self.l1._path()
		else:
			o += f".compose({self.l1._path()})"

		return o


@dataclass(frozen=True)
class LensAttr(ALens[O, T]):
	attr: str

	_has_path: ClassVar[bool] = True

	def _get(self, o: O) -> T:
		return getattr(o, self.attr)

	def _set(self, o: O, t: T) -> None:
		setattr(o, self.attr, t)

	def _path(self) -> str:
		return f".{self.attr}"


@dataclass(frozen=True)
class LensGetitem(ALens[O, T]):
	key: str
	default: Optional[T] = None

	_has_path: ClassVar[bool] = True

	def _get(self, o: O) -> T:
		if self.default is not None:
			try:
				return o.__getitem__(self.key)
			except KeyError:
				return self.default
		else:
			return o.__getitem__(self.key)

	def _set(self, o: O, t: T) -> None:
		return o.__setitem__(self.key, t)

	def _path(self) -> str:
		return f'["{self.key}"]'


class AManyLens(Generic[O, T]):
	"""A lens with many foci"""
	_has_path: ClassVar[bool] = False

	@abstractmethod
	def _get(self, o: O) -> Sequence[T]:
		"""Get the values"""

	@abstractmethod
	def _set(self, o: O, t: T) -> None:
		"""Set all foci to the same value"""

	def _bind(self, o: O) -> BoundLens[O, T]:
		return BoundLens(o, self)

	def _compose(self, l: ALens[O, T]):
		return LensManyComposed(self, l)

	def _path(self) -> str:
		return repr(self)

	def __getitem__(self, k: K) -> AManyLens[O, T]:
		return self._compose(LensGetitem(k))

	def __getattr__(self, item):
		return self._compose(LensAttr(item))

	def __mul__(self, other: O):
		return LensManyComposed(self, other)

	def __matmul__(self, other: O):
		return self._bind(other)

# class BoundManyLens(Generic[O, T]):
# 	def __init__(self, o: O, l: AManyLens[O, T]):
# 		self._o = o
# 		self._l = l
#
# 	def g(self) -> Sequence[T]:
# 		"""Get the values"""
# 		return self._l._get(self._o)
#
# 	def s(self, t: T) -> None:
# 		return self._l._set(self._o, t)
#
# 	def _m(self, f: Callable[[T], T]) -> None:
# 		for e in self._l:

@dataclass(frozen=True)
class LensElements(AManyLens[O, T]):
	"""A lens into all elements of a list"""

	def _get(self, o: O) -> T:
		return o

	def _set(self, o: O, t: T) -> None:
		for i, _ in enumerate(o):
			o[i] = t


@dataclass(frozen=True)
class LensManyComposed(AManyLens[O, T]):
	splitter: ALens[O, Sequence[U]]
	l1: ALens[U, T]

	def _get(self, o: O) -> Sequence[U]:
		return [self.l1._get(e) for e in self.splitter._get(o)]

	def _set(self, o: O, t: T):
		v0 = self.splitter._get(o)
		for e in v0:
			self.l1._set(e, t)
#
#
# @dataclass(frozen=True)
# class ALensMany()