from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

S = TypeVar("S")
T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")

U = TypeVar("U")

F = Callable[[A], B]
TupleOf = tuple[U, ...]


class Either(ABC, Generic[A, B]):
	pass


@dataclass
class Left(Either[A, B]):
	v: A


@dataclass
class Right(Either[A, B]):
	v: B


class Maybe(Generic[A]):
	pass


@dataclass
class Just(Maybe[A]):
	v: A


class Nothing(Maybe[A]):
	pass


class LensT(ABC, Generic[S, T, A, B]):
	@abstractmethod
	def view(self, s: S) -> A:
		pass

	@abstractmethod
	def update(self, b: B, s: S) -> T:
		pass


@dataclass
class LensIndex(LensT[S, T, A, B]):
	index: int

	def view(self, s: S) -> A:
		return s[self.index]

	def update(self, b: B, s: S) -> T:
		# make the reference positive to prevent s[-1:] from reversing the list
		idx = self.index if self.index >= 0 else len(s) + self.index
		return s.__class__((*s[:idx], b, *s[idx + 1 :]))


class PrismT(Generic[S, T, A, B]):
	@abstractmethod
	def match(self, s: S) -> Either[A, T]: ...

	@abstractmethod
	def build(self, b: B) -> T: ...


class PrismMaybe(PrismT[S, T, A, B]):
	def match(self, s: Maybe[S]) -> Either[A, T]:
		if isinstance(s, Just):
			return Left(s.v)
		else:
			return Right(None)

	def build(self, b: B) -> T:
		return Just(b)


class Affine(ABC, Generic[S, T, A, B]):
	def preview(self, s: S) -> Either[A, T]:
		pass

	def set(self, b: B, s: S) -> T:
		pass


class AffineFirst(Affine[list, list, A, B]):
	def preview(self, s: S) -> Either[A, T]:
		if len(s) > 0:
			return Left(s[0])
		else:
			return Right(None)

	def set(self, b: B, s: S) -> T:
		if len(s) > 0:
			return [b, *s[1:]]
		else:
			return []


class TraversalT(ABC, Generic[S, T, A, B]):
	@abstractmethod
	def contents(self, s: S) -> TupleOf[A]:
		pass

	@abstractmethod
	def fill(self, b: TupleOf[B], s: S) -> T:
		pass


class TraversalEnds(TraversalT[list, list, A, B]):
	def contents(self, s: S) -> TupleOf[A]:
		return (s[0], s[-1])

	def fill(self, b: TupleOf[B], s: S) -> T:
		return [b[0], *s[1:-1], b[1]]
