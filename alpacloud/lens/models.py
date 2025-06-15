from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

S = TypeVar("S")
T = TypeVar("T")
U = TypeVar("U")

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


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
class ComposedLens(LensT[S, U, A, C], Generic[S, T, U, A, B, C]):

	l1: LensT[S, T, A, B]
	l2: LensT[T, U, B, C]

	def get(self, s: S) -> A:
		return self.l2.get(self.l1.get(s))

	def set(self, s: S, b: B) -> T:
		return self.l1.set(
			s,
			self.l2.set(
				self.l1.get(s),
				b
			)
		)


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

@dataclass
class KeyLens(LensT[S, T, A, B]):
	key: str

	@property
	def name(self):
		return f"[{self.key}]"

	def get(self, s: S) -> A:
		return s[self.key]

	def set(self, s: S, b: B) -> T:
		o = copy(s)
		o[self.key] = b
		return o
