from alpacloud.lens.models import Lens, LensAttr, LensGetitem, LensElements


class C:
	def __init__(self):
		self.q = "q"
		self.w = "w"


class TestAttr:
	def test_get_present(self):
		c = C()
		assert LensAttr("q")._bind(c).g() == "q"

	def test_set_present(self):
		c = C()
		LensAttr("w")._bind(c).s("tgt")
		assert c.w == "tgt"


class TestGetitem:
	def test_get_present(self):
		c = {"q": "v"}
		assert LensGetitem("q")._bind(c).g() == "v"

	def test_get_absent_default(self):
		c = {"q": "v"}
		assert LensGetitem("w", "tgt")._bind(c).g() == "tgt"

	def test_set_present(self):
		c = {"q": "v"}
		LensGetitem("q")._bind(c).s("tgt")
		assert c["q"] == "tgt"

	def test_set_absent(self):
		c = {"q": "v"}
		LensGetitem("w")._bind(c).s("tgt")
		assert c["w"] == "tgt"


class TestCompose:
	def test_get(self):
		c = {"q0": {"q1": "v"}}
		l = LensGetitem("q0")._compose(LensGetitem("q1"))
		assert l._bind(c).g() == "v"

	def test_set(self):
		c = {"q0": {"q1": "v"}}
		l = LensGetitem("q0")._compose(LensGetitem("q1"))
		l._bind(c).s("tgt")
		assert c["q0"]["q1"] == "tgt"

	def test_getitem(self):
		c = {"q0": {"q1": "v"}}
		l = Lens()["q0"]["q1"]
		assert l._bind(c).g() == "v"

	def test_setitem(self):
		c = {"q0": {"q1": "v"}}
		l = Lens()["q0"]["q1"]
		l._bind(c).s("tgt")
		assert c["q0"]["q1"] == "tgt"

	def test_getattr(self):
		c = {"q0": C()}
		l = Lens()["q0"].q
		assert l._bind(c).g() == "q"

	def test_setattr(self):
		c = {"q0": C()}
		l = Lens()["q0"].q
		l._bind(c).s("tgt")
		assert c["q0"].q == "tgt"


class TestRepr:
	def test_some(self):
		l = Lens()["q0"].q
		assert l._path() == 'Lens()["q0"].q'

class TestSyntax:
	def test_compose(self):
		q = {"q0": {"q1": "v"}}
		l = LensGetitem("q0") * LensGetitem("q1")
		assert l._bind(q).g() == "v"

	def test_bind(self):
		q = {"q0": {"q1": "v"}}
		l = Lens()["q0"]["q1"]
		assert (l @ q).g() == "v"

class TestMulti:
	"""Tests for lenses that operate on multiple items"""

	# def test_get(self):
	# 	c = [1,2,3]
	# 	l = Lens

	def test_get(self):
		c = [1,2,3]
		l = LensElements()
		assert (l@c).g() == c

	def test_set(self):
		c = [1,2,3]
		l = LensElements()
		(l @ c).s(1)
		assert c == [1,1,1]

	def test_compose(self):
		c = [C(), C(), C()]
		l = LensElements().q
		assert (l @ c).g() == ["q", "q", "q"]

	def test_compose_set(self):
		c = [C(), C(), C()]
		b = LensElements().q @ c
		b.s(1)
		assert b.g() == [1,1,1]

	def test_compose_multiple(self):
		c = [[C(), C(), C()]]
		b = LensElements()._compose(LensElements()).q @ c
		print(b._l._path())
		b.s(1)
		assert b.g() == [1,1,1]