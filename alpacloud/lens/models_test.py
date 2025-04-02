from alpacloud.lens.models import LensAttr, LensGetitem, Lens


class C:
	def __init__(self):
		self.q = "q"
		self.w = "w"


class TestAttr:
	def test_get_present(self):
		c = C()
		assert LensAttr("q").bind(c).g() == "q"

	def test_set_present(self):
		c = C()
		LensAttr("w").bind(c).s("tgt")
		assert c.w == "tgt"


class TestGetitem:
	def test_get_present(self):
		c = {"q": "v"}
		assert LensGetitem("q").bind(c).g() == "v"

	def test_get_absent_default(self):
		c = {"q": "v"}
		assert LensGetitem("w", "tgt").bind(c).g() == "tgt"

	def test_set_present(self):
		c = {"q": "v"}
		LensGetitem("q").bind(c).s("tgt")
		assert c["q"] == "tgt"

	def test_set_absent(self):
		c = {"q": "v"}
		LensGetitem("w").bind(c).s("tgt")
		assert c["w"] == "tgt"


class TestCompose:
	def test_get(self):
		c = {"q0": {"q1": "v"}}
		l = LensGetitem("q0").compose(LensGetitem("q1"))
		assert l.bind(c).g() == "v"

	def test_set(self):
		c = {"q0": {"q1": "v"}}
		l = LensGetitem("q0").compose(LensGetitem("q1"))
		l.bind(c).s("tgt")
		assert c["q0"]["q1"] == "tgt"

	def test_getitem(self):
		c = {"q0": {"q1": "v"}}
		l = Lens()["q0"]["q1"]
		assert l.bind(c).g() == "v"

	def test_setitem(self):
		c = {"q0": {"q1": "v"}}
		l = Lens()["q0"]["q1"]
		l.bind(c).s("tgt")
		assert c["q0"]["q1"] == "tgt"

	def test_getattr(self):
		c = {"q0": C()}
		l = Lens()["q0"].q
		assert l.bind(c).g() == "q"

	def test_setattr(self):
		c = {"q0": C()}
		l = Lens()["q0"].q
		l.bind(c).s("tgt")
		assert c["q0"].q == "tgt"
