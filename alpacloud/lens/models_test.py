from __future__ import annotations

from dataclasses import dataclass

from alpacloud.lens.models import (
	AttrLens,
	BoundLensT,
	CodecLens,
	CombinedBoundLens,
	CombinedLens,
	ComposedLens,
	ConstLens,
	FilterLens,
	ForeachLens,
	IndexLens,
	KeyLens,
	Lens,
)

v = [0, 1, 2]
u = ["a", [0, 1, 2], "c"]
w = [["a", 0], ["b", 1], ["c", 2]]


@dataclass
class C:
	f: int


@dataclass
class M:
	s: str


c = C(1)


class TestIndex:
	def test_index(self):
		l = IndexLens(1)
		assert l.l_get(v) == 1
		assert l.l_set(v, 9) == [0, 9, 2]

	def test_index_end(self):
		l = IndexLens(-1)
		assert l.l_get(v) == 2
		assert l.l_set(v, 9) == [0, 1, 9]


class TestKey:
	d = {1: "1", 2: "2", 3: "3"}

	def test_key(self):
		l = KeyLens(1)
		assert l.l_get(self.d) == "1"
		assert l.l_set(self.d, "9") == {1: "9", 2: "2", 3: "3"}

	def test_key_default(self):
		l = KeyLens(0, "default")
		assert l.l_get(self.d) == "default"

	def test_key_default_mutable(self):
		l = KeyLens(0, {})

		v = (l / KeyLens(1)).l_set({}, 9)
		# assert v == {0:{1: 9}}
		assert v == {0: {1: 9}}

		w = (l / KeyLens(2)).l_set({}, 8)
		assert w == {0: {2: 8}}

		assert v == {0: {1: 9}}


class TestAttribute:
	def test_attribute(self):
		l = AttrLens("f")
		assert l.l_get(c) == 1
		assert l.l_set(c, 9) == C(9)


class TestComposed:
	matrix = [[M("00"), M("01"), M("02")], [M("10"), M("11"), M("12")], [M("20"), M("21"), M("22")]]

	def test_compose(self):
		l = ComposedLens(IndexLens(1), IndexLens(0))
		assert l.l_get(u) == 0
		assert l.l_set(u, 9) == ["a", [9, 1, 2], "c"]

	def test_multiple_compose(self):
		l0 = ComposedLens(ComposedLens(IndexLens(1), IndexLens(0)), AttrLens("s"))
		l1 = ComposedLens(IndexLens(1), ComposedLens(IndexLens(0), AttrLens("s")))

		assert l0.l_get(self.matrix) == l1.l_get(self.matrix)


class TestCombined:
	def test_combine(self):
		l = CombinedLens((IndexLens(0), IndexLens(1)))
		assert l.l_get(v) == [0, 1]
		assert l.l_set(v, 9) == [9, 9, 2]
		assert l.l_map(v, lambda x: x + 5) == [5, 6, 2]


class TestForEach:
	def test_for_each(self):
		l = ForeachLens(IndexLens(1))
		assert l.l_get(w) == [0, 1, 2]
		assert l.l_set(w, 9) == [["a", 9], ["b", 9], ["c", 9]]

	def test_map(self):
		l = ForeachLens(IndexLens(1))
		assert l.l_map(w, lambda x: x * 2) == [["a", 0], ["b", 2], ["c", 4]]

	def test_many_foreach(self):
		l = ForeachLens(ForeachLens(Lens()))

		assert l.l_set(w, 1) == [[1, 1], [1, 1], [1, 1]]
		assert l.l_map(w, lambda x: x * 2) == [["aa", 0], ["bb", 2], ["cc", 4]]

	def test_ops_after_foreach(self):
		l = ForeachLens(IndexLens(0)) / AttrLens("f")

		v = [[C(1)]]

		print(l)
		assert l.l_get(v) == [1]
		assert l.l_map(v, lambda x: x * 2) == [[C(2)]]


class TestCodec:
	csvlens: CodecLens[str, str, list, list] = CodecLens(
		dec=lambda s: s.split(","),
		enc=lambda es: ",".join(es),
		codec_name="csv",
	)
	str2intlens = CodecLens(
		dec=int,
		enc=str,
		codec_name="str2int",
	)

	def test_codec(self):
		s = "0,1,2"
		assert self.csvlens.l_get(s) == ["0", "1", "2"]
		assert self.csvlens.l_set(s, ["4", "5"]) == "4,5"
		assert self.csvlens.l_map(s, lambda es: es * 2) == "0,1,2,0,1,2"

	def test_codec_composed(self):
		s = "0,1,2"
		l = ComposedLens(self.csvlens, ForeachLens(self.str2intlens))

		assert l.l_get(s) == [0, 1, 2]
		assert l.l_set(s, 9) == "9,9,9"
		o = []

		def a(es):
			o.append(es)
			return es * 2

		assert l.l_map(s, a) == "0,2,4"


class TestFilter:
	v = [1, 2, 3]
	o = [1, 3, 5]

	@staticmethod
	def is_even(e):
		return e % 2 == 0

	def test_present(self):
		l = ForeachLens(FilterLens(self.is_even))
		assert l.l_get(self.v) == [None, 2, None]
		assert l.l_set(self.v, 9) == [1, 9, 3]
		assert l.l_map(self.v, lambda es: es * 2) == [1, 4, 3]

	def test_absent(self):
		l = ForeachLens(FilterLens(self.is_even))
		assert l.l_get(self.o) == [None, None, None]
		assert l.l_set(self.o, 9) == self.o
		assert l.l_map(self.o, lambda es: es * 2) == self.o

	def test_compose(self):
		w = [[0, 1, 2], [3, 4]]
		l = ForeachLens(FilterLens(lambda e: len(e) > 2)) / IndexLens(2)

		assert l.l_get(w) == [2, None]
		assert l.l_set(w, 9) == [[0, 1, 9], [3, 4]]
		assert l.l_map(w, lambda es: es * 2) == [[0, 1, 4], [3, 4]]


class TestBoundLens:
	def test_combined(self):
		l0 = BoundLensT.const(IndexLens(0), 9)
		l1 = BoundLensT.const(IndexLens(1), 8)
		v = [0, 1]

		combined = l0 % l1
		assert combined.map(v) == [9, 8]

	def test_combined_coalesce(self):
		"""Test that a CombinedBoundLens will be extended when combined with single items"""
		l0 = BoundLensT.const(IndexLens(0), 9)
		l1 = BoundLensT.const(IndexLens(1), 8)
		l2 = BoundLensT.const(IndexLens(2), 7)

		assert len(((l0 % l1) % l2).lenses) == 3
		assert len(((l0 % l1) % CombinedBoundLens((l2,))).lenses) == 2


class TestHelpers:
	v = [[1, "a"], [2, "b"], [3, C(9)], [4, [0, 1, 2]]]

	def test_getitem(self):
		l = IndexLens(1)
		assert l[1].l_get(self.v) == "b"

	def test_getattr(self):
		w = [C(0), C(9)]
		l = IndexLens(1)

		assert l.f.l_get(w) == 9

	def test_foreach(self):
		w = {"a": self.v}
		l = KeyLens("a")

		assert (l * IndexLens(0)).l_get(w) == [1, 2, 3, 4]

	def test_foreach_1(self):
		w = {"k0": [[0, 1], [2, 3]]}
		l = KeyLens("k0") * IndexLens(0)

		assert l.l_get(w) == [0, 2]

	def test_bind(self):
		s = {"a": w}
		l = KeyLens("a")

		def f(x):
			return x - 9

		assert (l * IndexLens(1) @ f).map(s) == {"a": [["a", -9], ["b", -8], ["c", -7]]}

	def test_compose(self):
		l1 = IndexLens(0)
		l2 = IndexLens(1)

		assert (l1 / l2).l_get(self.v) == "a"

	def test_combine(self):
		l1 = IndexLens(0)
		l2 = IndexLens(1)

		assert (l1 % l2).l_get(self.v) == [[1, "a"], [2, "b"]]

	def test_after_compose(self):
		l1 = IndexLens(0)
		l2 = IndexLens(1)

		l = (l1 % l2) * IndexLens(0)
		assert l.l_get(self.v) == [1, 2]

	def test_const(self):
		v = [0, 1, 2]
		l = IndexLens(1) / ConstLens(9)

		assert l.l_get(self.v) == 9
		assert l.l_set(v, 8) == [0, 9, 2]
		assert l.l_map(v, lambda es: es * 2) == [0, 9, 2]
