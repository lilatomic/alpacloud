import os
from pathlib import Path

import sh

from alpacloud.argocdkit.postrender import YamlDumper
from alpacloud.lens.conftest import ResourceLoader

res = ResourceLoader(Path(__file__).parent / "test_resources")

class TestPostrender:
	def test_postrender(self):
		rendered = sh.Command("helm")("template", "my-deployment", "./test_resources/testchart", '--post-renderer=./test_resources/my_postrenderer.py')

		expected = res.load_objs("expected")
		assert YamlDumper.safe_load_all(rendered) == expected