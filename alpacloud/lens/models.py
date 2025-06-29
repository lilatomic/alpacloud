"""
Lenses are a generalised representation of accessing data.
This representation is then something we can reuse and pass around.
For example, when modifying a value of a key in a dictionary,
we might have code like the following:
`my_dict["my_key"] = my_dict["my_key"] * 2`
Note that we have to write out `my_dict["my_key"]` twice, even though they're the same.
Lenses allow us to represent this as a object we can manipulate:
```
my_key = KeyLens("my_key")
my_key.l_set(my_dict, my_key.l_get(my_dict) * 2)
```
In this case, this doesn't result in much compression.
However, for no additional complexity in the invocation,
the lens could involve many components, filters, and codecs.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Callable, Generic, Hashable, Type, TypeVar

from alpacloud.lens.util.sentinel import Sentinel

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
	"""Compose 2 lenses."""
	return ComposedLens(l1, l2)


class LensT(Generic[S, T, A, B], ABC):
	"""
	A generalised representation of accessing data.

	Methods of Lenses are prefixed with `l_`.
	This makes them less likely to conflict with properties,
	which allows convenient `thing.property` syntax.
	"""

	@property
	@abstractmethod
	def l_name(self) -> str:
		"""The name of the current lens."""

	@abstractmethod
	def l_get(self, s: S) -> A:
		"""Get the focus of this lens."""

	@abstractmethod
	def l_set(self, s: S, b: B) -> T:
		"""Set the focus of this lens."""

	def l_map(self, s: S, f: F):
		"""Transform the focus of this lens."""
		return self.l_set(s, f(self.l_get(s)))

	def l_compose(self, other: LensT[T, U, B, C]) -> LensT[S, U, A, C]:
		"""Compose this lens with another one sequentially."""
		return compose(self, other)

	def l_bind(self, f: F) -> BoundLens[S, T, A, B]:
		"""
		Bind a mapping function to this lens.
		This allows binding the result of transformations,
		so they can be accumulated into a large transformation.
		"""
		return BoundLens(self, f)

	def __getitem__(self, k: K):
		return self.l_compose(KeyLens(k))

	def __getattr__(self, item):
		if item.startswith("__") and item.endswith("__"):
			super().__getattribute__(item)
		return self.l_compose(PropLens(item))

	def __mul__(self, other):
		"""
		Apply the next lens on each element of the focus.

		>>> w = {"k0": [[0, 1], [2, 3]]}
		>>> l = KeyLens("k0") * IndexLens(0)
		>>> l.l_get(w)
		[0, 2]
		"""
		return self.l_compose(ForeachLens(other))

	def __matmul__(self, f: F):
		"""
		Bind this lens with a mapping function.
		"""
		return BoundLens(self, f)

	def __truediv__(self, other):
		"""Compose this lens with another one sequentially."""
		return self.l_compose(other)

	def __mod__(self, other):
		"""
		Combine these lenses in parallel.

		>>> w = [[0,1], [2,3]]
		>>> l01 = IndexLens(0) / IndexLens(1)
		>>> l10 = IndexLens(1) / IndexLens(0)
		>>> l = l01 % l10
		>>> l.l_get(w)
		[1, 2]
		"""
		return CombinedLens((self, other))


@dataclass
class Const(Generic[B]):
	v: B

	def __call__(self, *args, **kwargs) -> B:
		return self.v


class BoundLensT(Generic[S, T, A, B], ABC):
	"""A generalised representation of modifying data."""

	def __mod__(self, other: BoundLensT[S, T, A, B]):
		"""Combine these bound lenses in parallel."""
		return CombinedBoundLens((self, other))

	def map(self, s: S) -> T:
		"""Modify the focus of this lens."""

	@staticmethod
	def const(l: LensT[S, T, A, B], v: B) -> BoundLens[S, T, A, B]:
		"""Set the focus of this lens to a constant value."""

		def _const(_: A) -> B:
			return v

		return BoundLens(l, _const)


@dataclass
class BoundLens(BoundLensT[S, T, A, B]):
	"""A generalised representation of modifying data."""

	lens: LensT[S, T, A, B]
	f: F

	def get(self, s: S) -> A:
		"""Get the focus of this lens. Useful for debugging."""
		return self.lens.l_get(s)

	def map(self, s: S) -> T:
		return self.lens.l_map(s, self.f)


@dataclass
class CombinedBoundLens(BoundLensT[S, T, A, B]):
	"""A generalised representation of modifying data with multiple transforms."""

	lenses: TupleOf[BoundLensT[S, T, A, B]]

	def map(self, s: S) -> T:
		for lens in self.lenses:
			s = lens.map(s)
		return s

	def __mod__(self, other: BoundLensT[S, T, A, B]):
		"""
		Combine this bound lens with another bound lens.
		Will coalesce when provided with a single BoundLens,
		or create a tree when provided with a CombinedBoundLens.
		"""
		if isinstance(other, BoundLens):
			return CombinedBoundLens((*self.lenses, other))
		else:
			return CombinedBoundLens((self, other))


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
	"""Lenses applied sequentially."""

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

	def l_compose(self, other: LensT[T, U, B, C]) -> LensT[S, U, A, C]:
		"""
		This composes with the last item in the composition.
		This allows lenses with special compositional rules/helpers, like ForEachLens, to implement those.
		"""
		return ComposedLens(self.l1, self.l2.l_compose(other))


@dataclass
class CombinedLens(LensT[S, T, A, B]):
	"""Lenses combined in parallel. The resulting lens will have multiple objects focused"""

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
	"""Lens which focuses an attribute of an object. Equivalent to `object.attribute`"""

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
	"""Lens which gets an item from a collection, equivalent to `object[index]`"""

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
	"""Get a key from a dictionary"""

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


def append(a: A) -> Callable:
	"""Append an item to the collection"""

	def _append(m):
		m.append(a)  # TODO: idempotency
		return m

	return _append


@dataclass
class ForeachLens(LensT[S, T, A, B]):
	"""
	Apply lenses to each item focused.

	>>> w = [[1, 2], [3, 4]]
	>>> l = ForeachLens(IndexLens(0))
	>>> l.l_get(w)
	[1, 3]

	You can also get this lens with the `*` helper:
	>>> l0 = IdentityLens() * IndexLens(1)
	>>> l0.l_get(w)
	[2, 4]
	"""

	l: LensT[S, T, A, B]

	@property
	def l_name(self) -> str:
		return f"[*{self.l.l_name}]"

	def l_get(self, s: S) -> A:
		return list(map(self.l.l_get, s))

	def l_set(self, s: S, b: B) -> T:
		return list(map(lambda e: self.l.l_set(e, b), s))

	def l_map(self, s: S, f: Callable[[A], B]) -> T:
		return list(map(lambda e: self.l.l_map(e, f), s))

	def l_compose(self, other: LensT[T, U, B, C]) -> LensT[S, U, A, C]:
		return ForeachLens(self.l.l_compose(other))


class CodecLensABC(LensT[S, T, A, B], Generic[S, T, A, B, C], ABC):
	"""
	A lens that decodes and re-encodes an object.

	This is often used for decoding representations, like JSON parsing a string.
	This is also used for unpacking strings, like parsing a url.
	"""

	def dec(self, a: A) -> C:
		"""Decode the value"""

	def enc(self, c: C) -> B:
		"""Encode the value into the target type"""

	@staticmethod
	def _fmt_name(name: str) -> str:
		return f"|({name})"

	def l_get(self, s: S) -> A:
		return self.dec(s)

	def l_set(self, s: S, b: B) -> T:
		return self.enc(b)


@dataclass
class CodecLens(CodecLensABC, Generic[S, T, A, B, C]):
	"""A lens that decodes and re-encodes its focus."""

	dec: Callable[[A], C]

	enc: Callable[[C], B]
	codec_name: str = "codec"

	@property
	def l_name(self) -> str:
		return super()._fmt_name(self.codec_name)


def DataclassCodec(cls: Type) -> CodecLens:
	"""Turn a dict into a dataclass"""
	return CodecLens(
		dec=lambda d: cls(**d),
		enc=dataclasses.asdict,
		codec_name=f"DataclassCodec({cls.__name__})",
	)


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
