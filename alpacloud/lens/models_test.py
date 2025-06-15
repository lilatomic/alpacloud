from __future__ import annotations

from dataclasses import dataclass

from alpacloud.lens.models import CodecLens, ComposedLens, FilterLens, ForeachLens, IdentityLens, IndexLens, KeyLens, PropLens

v = [0, 1, 2]
u = ["a", [0, 1, 2], "c"]
w = [["a", 0], ["b", 1], ["c", 2]]


@dataclass
class C:
	f: int


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


class TestAttribute:
	def test_attribute(self):
		l = PropLens("f")
		assert l.l_get(c) == 1
		assert l.l_set(c, 9) == C(9)


class TestComposed:
	def test_compose(self):
		l = ComposedLens(IndexLens(1), IndexLens(0))
		assert l.l_get(u) == 0
		assert l.l_set(u, 9) == ["a", [9, 1, 2], "c"]


class TestForEach:
	def test_for_each(self):
		l = ForeachLens(IndexLens(1))
		assert l.l_get(w) == [0, 1, 2]
		assert l.l_set(w, 9) == [["a", 9], ["b", 9], ["c", 9]]

	def test_map(self):
		l = ForeachLens(IndexLens(1))
		assert l.l_map(w, lambda x: x * 2) == [["a", 0], ["b", 2], ["c", 4]]

	def test_many_foreach(self):
		l = ForeachLens(ForeachLens(IdentityLens()))

		assert l.l_set(w, 1) == [[1, 1], [1, 1], [1, 1]]
		assert l.l_map(w, lambda x: x * 2) == [["aa", 0], ["bb", 2], ["cc", 4]]


class TestCodec:
	csvlens = CodecLens(
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

	def test_bind(self):
		w = {"a": self.v}
		l = KeyLens("a")

		assert (l * IndexLens(0) @ w).get() == [1, 2, 3, 4]
