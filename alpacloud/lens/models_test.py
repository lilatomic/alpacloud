from __future__ import annotations
from dataclasses import dataclass

from alpacloud.lens.models import IndexLens, PropLens

v = [0,1,2]

@dataclass
class C:
	f: int

c = C(1)


class TestIndex:
	def test_index(self):
		l = IndexLens(1)
		assert l.get(v) == 1
		assert l.set(v, 9) == [0,9,2]

	def test_index_end(self):
		l = IndexLens(-1)
		assert l.get(v) == 2
		assert l.set(v, 9) == [0,1,9]

class TestAttribute:
	def test_attribute(self):
		l = PropLens("f")
		assert l.get(c) == 1
		assert l.set(c, 9) == C(9)
