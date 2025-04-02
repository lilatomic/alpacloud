from alpacloud.lens.models import LensAttr, LensGetitem


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
		assert LensGetitem("w", "tgt").bind(c).g() is "tgt"

	def test_set_present(self):
		c = {"q": "v"}
		LensGetitem("q").bind(c).s("tgt")
		assert c["q"] == "tgt"

	def test_set_absent(self):
		c = {"q": "v"}
		LensGetitem("w").bind(c).s("tgt")
		assert c["w"] == "tgt"

