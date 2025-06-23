from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from alpacloud.lens.conftest import StrStartsWith
from alpacloud.lens.k8s import Image, ImageCodec, decode_image, deployment_labels, encode_image, image, xdict


@dataclass
class ResourceLoader:
	base_path: Path

	def load_obj(self, name: str):
		return yaml.safe_load((self.base_path / name).open())

	def __getitem__(self, item):
		return self.load_obj(item + ".yml")


res = ResourceLoader(Path(__file__).parent / "test_resources")


class TestHelpers:
	def test_xdict(self):
		a = {"1": 1, "2": 2}
		b = {"3": 3, "4": 4}
		assert xdict(a)(b) == xdict(b)(a)
		assert len(xdict(a)(b)) == 4


class TestDeployment:
	def test_set_labels(self):
		matchlabels = {
			"l1": "v1",
			"l2": "v2",
		}

		l = deployment_labels @ (xdict(matchlabels))

		r = l.map(res["deployment"])

		a = deployment_labels.l_get(r)
		[a0, a1] = a
		assert matchlabels.items() <= a0.items()
		assert matchlabels.items() <= a1.items()


class TestDockerImageParsing:
	@pytest.mark.parametrize(
		"input_str, expected",
		[
			# Null case, useful for creating
			("", Image("docker.io", "", "latest")),
			# Simple cases
			("ubuntu", Image("docker.io", "ubuntu", "latest")),
			("ubuntu:20.04", Image("docker.io", "ubuntu", "20.04")),
			("library/ubuntu", Image("docker.io", "library/ubuntu", "latest")),
			("library/ubuntu:latest", Image("docker.io", "library/ubuntu", "latest")),
			# Two-component repo
			("myrepo/myimage:1.2", Image("docker.io", "myrepo/myimage", "1.2")),
			# Three-component repo
			("myorg/project/image", Image("docker.io", "myorg/project/image", "latest")),
			("myorg/project/image:3.5", Image("docker.io", "myorg/project/image", "3.5")),
			# With custom registries
			("gcr.io/org/project/img", Image("gcr.io", "org/project/img", "latest")),
			("gcr.io/org/project/img:v1.0.0", Image("gcr.io", "org/project/img", "v1.0.0")),
			# With digests
			("ubuntu@sha256:abcd", Image("docker.io", "ubuntu", "latest", "sha256:abcd")),
			("gcr.io/proj/img@sha256:beef", Image("gcr.io", "proj/img", "latest", "sha256:beef")),
			("myrepo/myimage:1.2@sha256:1234", Image("docker.io", "myrepo/myimage", "1.2", "sha256:1234")),
			# Deep path with tag and digest
			("ghcr.io/org/project/image:dev@sha256:feed", Image("ghcr.io", "org/project/image", "dev", "sha256:feed")),
			# Local registry with nested repository
			("localhost:5000/org/team/image", Image("localhost:5000", "org/team/image", "latest")),
			("localhost:5000/org/team/image:9", Image("localhost:5000", "org/team/image", "9")),
			("localhost:5000/org/team/image:9@sha256:cafe", Image("localhost:5000", "org/team/image", "9", "sha256:cafe")),
		],
	)
	def test_decode_and_roundtrip(self, input_str, expected):
		decoded = decode_image(input_str)
		assert decoded == expected

		# Round-trip: decode → encode → decode
		print(encode_image(decoded))
		round_trip = decode_image(encode_image(decoded))
		assert round_trip == decoded


class TestPod:
	def test_replace_image(self):
		l = image("nginx") @ ImageCodec.set_registry("localhost:4567")

		p = res["pod"]

		r = l.map(p)
		assert StrStartsWith("localhost:4567", r["spec"]["containers"][0]["image"]).check()
