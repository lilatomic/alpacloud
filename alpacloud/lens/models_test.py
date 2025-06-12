from alpacloud.lens.models import LensIndex, TraversalEnds


class TestIndex:
	v = [0, 1, 2]

	def test_in_range(self):
		l = LensIndex(1)
		assert l.view(self.v) == 1
		assert l.update(9, self.v) == [0, 9, 2]
		assert self.v == [0, 1, 2], "value should be unchanged"

	def test_at_beginning(self):
		l = LensIndex(0)
		assert l.view(self.v) == 0
		assert l.update(9, self.v) == [9, 1, 2]
		assert self.v == [0, 1, 2], "value should be unchanged"

	def test_at_end(self):
		l = LensIndex(2)
		assert l.view(self.v) == 2
		assert l.update(9, self.v) == [0, 1, 9]
		assert self.v == [0, 1, 2], "value should be unchanged"

	def test_from_beginning(self):
		"""Test that `-1` works."""
		l = LensIndex(-1)
		assert l.view(self.v) == 2
		assert l.update(9, self.v) == [0, 1, 9]
		assert self.v == [0, 1, 2], "value should be unchanged"

	def test_with_tuple(self):
		"""Test that listlike things remain themselves."""
		l = LensIndex(1)
		r = l.update(9, tuple([0, 1, 2]))
		assert isinstance(r, tuple)
		assert r == (0, 9, 2)


class TestTraversal:
	def test_contents(self):
		v = [1, 2, 3]
		t = TraversalEnds()
		contents = t.contents(v)
		assert contents == (1, 3)

	def test_fill(self):
		v = [1, 2, 3]
		t = TraversalEnds()
		filled = t.fill((8, 9), v)
		assert filled == [8, 2, 9]
