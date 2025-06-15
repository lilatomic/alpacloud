from __future__ import annotations

from dataclasses import dataclass

from alpacloud.lens.models import ComposedLens, ForeachLens, IdentityLens, IndexLens, PropLens, CodecLens

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
		assert l.get(v) == 1
		assert l.set(v, 9) == [0, 9, 2]

	def test_index_end(self):
		l = IndexLens(-1)
		assert l.get(v) == 2
		assert l.set(v, 9) == [0, 1, 9]


class TestAttribute:
	def test_attribute(self):
		l = PropLens("f")
		assert l.get(c) == 1
		assert l.set(c, 9) == C(9)


class TestComposed:
	def test_compose(self):
		l = ComposedLens(IndexLens(1), IndexLens(0))
		assert l.get(u) == 0
		assert l.set(u, 9) == ["a", [9, 1, 2], "c"]


class TestForEach:
	def test_for_each(self):
		l = ForeachLens(IndexLens(1))
		assert l.get(w) == [0, 1, 2]
		assert l.set(w, 9) == [["a", 9], ["b", 9], ["c", 9]]

	def test_map(self):
		l = ForeachLens(IndexLens(1))
		assert l.map(w, lambda x: x * 2) == [["a", 0], ["b", 2], ["c", 4]]

	def test_many_foreach(self):
		l = ForeachLens(ForeachLens(IdentityLens()))

		assert l.set(w, 1) == [[1, 1], [1, 1], [1, 1]]
		assert l.map(w, lambda x: x * 2) == [["aa", 0], ["bb", 2], ["cc", 4]]

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
		assert self.csvlens.get(s) == ["0","1","2"]
		assert self.csvlens.set(s, ["4","5"]) == "4,5"
		assert self.csvlens.map(s, lambda es: es*2) == "0,1,2,0,1,2"

	def test_codec_composed(self):
		s = "0,1,2"
		l = ComposedLens(self.csvlens, ForeachLens(self.str2intlens))

		assert l.get(s) == [0,1,2]
		assert l.set(s, 9) == "9,9,9"
		o = []

		def a(es):
			o.append(es)
			return es * 2

		assert l.map(s, a) == "0,2,4"
