from __future__ import annotations

from asyncio import Protocol
from typing import Callable, Dict, Generic, Hashable, Iterable, TypeVar, Union

S = TypeVar("S")
T = TypeVar("T")
U = TypeVar("U")

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
E = TypeVar("E")

K = TypeVar("K", bound=Hashable)

# Iterables of the above (I think Functors would also work
AM = TypeVar("AM", bound=Iterable)
BM = TypeVar("BM", bound=Iterable)
CM = TypeVar("CM", bound=Callable)

SM = TypeVar("SM", bound=Iterable)
TM = TypeVar("TM", bound=Iterable)
UM = TypeVar("UM", bound=Iterable)

# Dicts of the above
SD = TypeVar("SD", bound=Dict)
TD = TypeVar("TD", bound=Dict)

F = Callable[[A], B]
TupleOf = tuple[U, ...]


class SupportsIndex(Protocol, Generic[A]):
	def __getitem__(self, k):
		pass

	def __setitem__(self, k, v):
		pass

	def get(self, k, default):
		pass


JSONPrimitive = Union[str, int, float, bool, None]
JSONT = Union[JSONPrimitive, list["JSONT"], dict[str, "JSONT"]]
