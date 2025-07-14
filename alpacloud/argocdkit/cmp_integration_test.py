from dataclasses import dataclass
from typing import Any

import pytest

from alpacloud.argocdkit.cmp import CMP, ExceptionGroup, S
from alpacloud.argocdkit.spec import Plugin
from alpacloud.lens.util.type import JSONT


@dataclass
class MyCMP(CMP):
	result: Any = None

	@property
	def spec(self) -> Plugin:
		pass

	def parse_params(self, params):
		assert isinstance(params, dict)
		return super().parse_params(params)

	def parse_env(self, env: JSONT) -> S:
		assert isinstance(env, dict)
		return super().parse_env(env)

	def generate(self, app, params, plugin_env):
		self.result = (
			app,
			params,
			plugin_env,
		)


class TestErrors:
	def test_bad_params(self):
		c = MyCMP()
		with pytest.raises(ExceptionGroup) as e:
			c.run({}, "not a dict", {})
		assert len(e.value.exceptions) == 1

	def test_bad_plugin_env(self):
		c = MyCMP()
		with pytest.raises(ExceptionGroup) as e:
			c.run({}, {}, "not a dict")
		assert len(e.value.exceptions) == 1

	def test_multiple_bad(self):
		c = MyCMP()
		with pytest.raises(ExceptionGroup) as e:
			c.run({}, "not a dict", "not a dict")
		assert len(e.value.exceptions) == 2
