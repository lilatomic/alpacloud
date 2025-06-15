from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Hashable

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
	pass


class LensT(Generic[S, T, A, B], ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		pass

	@abstractmethod
	def get(self, s: S) -> A:
		pass

	@abstractmethod
	def set(self, s: S, b: B) -> T:
		pass

	def map(self, s: S, f: Callable[[A], B]):
		return self.set(s, f(self.get(s)))

	def compose(self, other: LensT[T, U, B, C]) -> LensT[S, U, A, C]:
		return compose(self, other)

	def bind(self, s: S) -> BoundLens[S, T, A, B]:
		return BoundLens(self, s)


@dataclass
class BoundLens(Generic[S, T, A, B]):
	lens: LensT[S, T, A, B]
	s: S

	def get(self) -> A:
		return self.lens.get(self.s)

	def set(self, b: B) -> T:
		return self.lens.set(self.s, b)

	def map(self, f: Callable[[A], B]) -> T:
		return self.lens.set(self.s, f(self.get()))


@dataclass
class IdentityLens(LensT[S, T, A, B]):
	"""A lens that just gets the current thing. Useful for terminating multilenses."""

	@property
	def name(self) -> str:
		return ""

	def get(self, s: S) -> A:
		return s

	def set(self, s: S, b: B) -> T:
		return b


@dataclass
class ComposedLens(LensT[S, U, A, C], Generic[S, T, U, A, B, C]):
	l1: LensT[S, T, A, B]
	l2: LensT[T, U, B, C]

	@property
	def name(self) -> str:
		return self.l1.name + self.l2.name

	def get(self, s: S) -> A:
		return self.l2.get(self.l1.get(s))

	def set(self, s: S, b: B) -> T:
		return self.l1.set(s, self.l2.set(self.l1.get(s), b))

	def map(self, s: S, f: Callable[[A], B]):
		return self.l1.set(s, self.l2.map(self.l1.get(s), f))

@dataclass
class PropLens(LensT[S, T, A, B]):
	prop: str

	@property
	def name(self):
		return f".{self.prop}"

	def get(self, s: S) -> A:
		return getattr(s, self.prop)

	def set(self, s: S, b: B) -> T:
		setattr(s, self.prop, b)
		return s


@dataclass
class IndexLens(LensT[S, T, A, B]):
	index: int

	@property
	def name(self):
		return f"[{self.index}]"

	def get(self, s: S) -> A:
		return s[self.index]

	def set(self, s: S, b: B) -> T:
		o = copy(s)
		o[self.index] = b
		return o


KEYERROR = Sentinel("KEYERROR")


@dataclass
class KeyLens(LensT[S, T, A, B], Generic[S, T, A, B, K]):
	key: K
	default: A | KEYERROR = KEYERROR

	@property
	def name(self):
		return f"[{self.key}]"

	def get(self, s: S) -> A:
		if self.default is KEYERROR:
			return s[self.key]
		else:
			return s.get(self.key, self.default)

	def set(self, s: S, b: B) -> T:
		o = copy(s)
		o[self.key] = b
		return o


@dataclass
class ForeachLens(LensT[S, T, A, B]):
	l: LensT[S, T, A, B]

	@property
	def name(self) -> str:
		return "[*]" + self.l.name

	def get(self, s: S) -> A:
		return list(map(self.l.get, s))

	def set(self, s: S, b: B) -> T:
		return list(map(lambda e: self.l.set(e, b), s))

	def map(self, s: S, f: Callable[[A], B]) -> T:
		return list(map(lambda e: self.l.map(e, f), s))


@dataclass
class CodecLens(LensT[S, T, A, B], Generic[S, T, A, B, C]):
	"""A lens which unpacks a value to index into it"""

	dec: Callable[[A], C]
	enc: Callable[[C], B]
	codec_name: str = "codec"

	@property
	def name(self) -> str:
		return f"|({self.codec_name})"

	def get(self, s: S) -> A:
		return self.dec(s)

	def set(self, s: S, b: B) -> T:
		return self.enc(b)
