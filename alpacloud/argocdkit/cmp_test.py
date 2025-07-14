import json
from pathlib import Path

from alpacloud.argocdkit.cmp import CMP, App, T, S, load_params, load_plugin_env
from alpacloud.lens.conftest import ResourceLoader

res = ResourceLoader(Path(__file__).parent / "test_resources")
envvars = res.load_obj("envvars.sample.json")

class MyCMP(CMP):

	def generate(self, app: App, params: T, plugin_env: S) -> str:
		pass


def test_parse_params():
	c = MyCMP()
	assert c.parse_params(load_params(envvars)) == {"postRenderers": ["/bin/my_postrenderer"]}

def test_parse_params_empty():
	c = MyCMP()
	assert c.parse_params(load_params({"ARGOCD_APP_PARAMETERS": "null"})) == {}

def test_parse_env():
	c = MyCMP()
	assert c.parse_env(load_plugin_env(envvars)) == {"foo": "bar"}
