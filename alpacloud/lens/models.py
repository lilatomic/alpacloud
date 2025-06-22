from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Callable, Generic, Hashable, TypeVar

from alpacloud.lens.util.sentinel import Sentinel

# TODO: try removing set to make implementing multilenses easier
# Implement set in terms of map and Const

S = TypeVar("S")
T = TypeVar("T")
U = TypeVar("U")

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")

K = TypeVar("K", bound=Hashable)

F = Callable[[A], B]
TupleOf = tuple[U, ...]


def compose(l1: LensT[S, T, A, B], l2: LensT[T, U, B, C]) -> LensT[S, U, A, C]:
	return ComposedLens(l1, l2)


class LensT(Generic[S, T, A, B], ABC):
	@property
	@abstractmethod
	def l_name(self) -> str:
		pass

	@abstractmethod
	def l_get(self, s: S) -> A:
		pass

	@abstractmethod
	def l_set(self, s: S, b: B) -> T:
		pass

	def l_map(self, s: S, f: F):
		return self.l_set(s, f(self.l_get(s)))

	def l_compose(self, other: LensT[T, U, B, C]) -> LensT[S, U, A, C]:
		return compose(self, other)

	def l_bind(self, f: F) -> BoundLens[S, T, A, B]:
		return BoundLens(self, f)

	def __getitem__(self, k: K):
		return self.l_compose(KeyLens(k))

	def __getattr__(self, item):
		return self.l_compose(PropLens(item))

	def __mul__(self, other):
		return self.l_compose(ForeachLens(other))

	def __matmul__(self, f: F):
		return BoundLens(self, f)

	def __truediv__(self, other):
		return self.l_compose(other)

	def __mod__(self, other):
		return CombinedLens((self, other))


@dataclass
class BoundLens(Generic[S, T, A, B]):
	lens: LensT[S, T, A, B]
	f: F

	def get(self, s: S) -> A:
		return self.lens.l_get(s)

	def map(self, s: S) -> T:
		return self.lens.l_map(s, self.f)


@dataclass
class IdentityLens(LensT[S, T, A, B]):
	"""A lens that just gets the current thing. Useful for terminating multilenses."""

	@property
	def l_name(self) -> str:
		return ""

	def l_get(self, s: S) -> A:
		return s

	def l_set(self, s: S, b: B) -> T:
		return b


@dataclass
class ConstLens(LensT[S, T, A, A]):
	"""A lens that always gives the same result. Useful for binding values to lenses"""

	v: A

	@property
	def l_name(self) -> str:
		return f"const({self.v})"

	def l_get(self, s: S) -> A:
		return self.v

	def l_set(self, s: S, b: B) -> T:
		return self.v

	def l_map(self, s: S, f: Callable[[A], B]):
		return self.l_set(s, self.v)


@dataclass
class ComposedLens(LensT[S, U, A, C], Generic[S, T, U, A, B, C]):
	l1: LensT[S, T, A, B]
	l2: LensT[T, U, B, C]

	@property
	def l_name(self) -> str:
		return self.l1.l_name + self.l2.l_name

	def l_get(self, s: S) -> A:
		return self.l2.l_get(self.l1.l_get(s))

	def l_set(self, s: S, b: B) -> T:
		return self.l1.l_set(s, self.l2.l_set(self.l1.l_get(s), b))

	def l_map(self, s: S, f: Callable[[A], B]):
		return self.l1.l_set(s, self.l2.l_map(self.l1.l_get(s), f))


@dataclass
class CombinedLens(LensT[S, T, A, B]):
	lenses: tuple[LensT[S, T, A, B], ...]
	combined_name: str | None = None

	@property
	def l_name(self) -> str:
		if self.combined_name is not None:
			return f"({self.combined_name})"
		else:
			return f"({len(self.lenses)} lenses)"

	def l_get(self, s: S) -> A:
		return [l.l_get(s) for l in self.lenses]

	def l_set(self, s: S, b: B) -> T:
		for l in self.lenses:
			s = l.l_set(s, b)
		return s

	def l_map(self, s: S, f: Callable[[A], B]):
		for l in self.lenses:
			s = l.l_map(s, f)
		return s


@dataclass
class PropLens(LensT[S, T, A, B]):
	prop: str

	@property
	def l_name(self):
		return f".{self.prop}"

	def l_get(self, s: S) -> A:
		return getattr(s, self.prop)

	def l_set(self, s: S, b: B) -> T:
		setattr(s, self.prop, b)
		return s


@dataclass
class IndexLens(LensT[S, T, A, B]):
	index: int

	@property
	def l_name(self):
		return f"[{self.index}]"

	def l_get(self, s: S) -> A:
		return s[self.index]

	def l_set(self, s: S, b: B) -> T:
		o = copy(s)
		o[self.index] = b
		return o


KEYERROR = Sentinel("KEYERROR")


@dataclass
class KeyLens(LensT[S, T, A, B], Generic[S, T, A, B, K]):
	key: K
	default: A | KEYERROR = KEYERROR

	@property
	def l_name(self):
		return f"[{self.key}]"

	def l_get(self, s: S) -> A:
		if self.default is KEYERROR:
			return s[self.key]
		else:
			return s.get(self.key, copy(self.default))  # TODO: maybe don't always copy, or default_factory

	def l_set(self, s: S, b: B) -> T:
		o = copy(s)
		o[self.key] = b
		return o


def kord(k: K) -> KeyLens:
	"""Get the key, with a dict for the default"""
	return KeyLens(k, {})


def korl(k: K) -> KeyLens:
	"""Get the key, with a list for the default"""
	return KeyLens(k, [])


@dataclass
class ForeachLens(LensT[S, T, A, B]):
	l: LensT[S, T, A, B]

	@property
	def l_name(self) -> str:
		return "[*]" + self.l.l_name

	def l_get(self, s: S) -> A:
		return list(map(self.l.l_get, s))

	def l_set(self, s: S, b: B) -> T:
		return list(map(lambda e: self.l.l_set(e, b), s))

	def l_map(self, s: S, f: Callable[[A], B]) -> T:
		return list(map(lambda e: self.l.l_map(e, f), s))


class CodecLensABC(LensT[S, T, A, B], Generic[S, T, A, B, C]):

	codec_name: str

	def dec(self, a: A) -> C:
		"""Decode the value"""

	def enc(self, c: C) -> B:
		"""Encode the value into the target type"""

	@property
	def l_name(self) -> str:
		return f"|({self.codec_name})"

	def l_get(self, s: S) -> A:
		return self.dec(s)

	def l_set(self, s: S, b: B) -> T:
		return self.enc(b)


@dataclass
class CodecLens(CodecLensABC, Generic[S, T, A, B, C]):
	"""A lens which unpacks a value to index into it"""

	dec: Callable[[A], C]
	enc: Callable[[C], B]
	codec_name: str = "codec"


@dataclass
class FilterLens(LensT[S, T, A, B]):
	"""A lens which will have a focus if its predicate matches"""

	predicate: Callable[[A], bool]
	predicate_name: str = "filter"

	@property
	def l_name(self) -> str:
		return f"?({self.predicate_name})"

	def l_get(self, s: S) -> A:
		if self.predicate(s):
			return s
		else:
			return None

	def l_set(self, s: S, b: B) -> T:
		if self.predicate(s):
			return b
		else:
			return s

	def l_map(self, s: S, f: Callable[[A], B]):
		if self.predicate(s):
			return f(s)
		else:
			return s
