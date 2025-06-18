from dataclasses import dataclass
from pathlib import Path

import yaml

from alpacloud.lens.k8s import deployment_labels, xdict


@dataclass
class ResourceLoader:
	base_path: Path

	def load_obj(self, name: str):
		return yaml.safe_load((self.base_path / name).open())

	def __getitem__(self, item):
		return self.load_obj(item + ".yml")

res = ResourceLoader(Path(__file__).parent / "test_resources")


class TestDeployment:
	def test_set_labels(self):
		matchlabels = {
			"l1": "v1",
			"l2": "v2",
		}

		l = deployment_labels @ (xdict(matchlabels))

		r = l.map(res["deployment"])

		a = deployment_labels.l_get(r)
		assert not a
		assert matchlabels.items() <= a0.items()
		assert matchlabels.items() <= a1.items()

