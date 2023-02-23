#!/usr/bin/env python
"""Run Ansibel integration tests"""
import os.path
import shutil
import subprocess
from tempfile import TemporaryDirectory


def output(b: bytes) -> None:
	"""Print helper"""
	o = b.decode("utf-8").replace("\\n", "\n")
	print(o)


def integration_test():
	"""Run Ansibel integration tests"""
	test_dir = TemporaryDirectory()

	collection_root_dir = os.path.join(test_dir.name, "ansible_collections")
	collection_dir = os.path.join(collection_root_dir, "lilatomic/azcli")
	shutil.copytree("lilatomic/azcli", collection_dir)
	result = subprocess.run(
		["ansible-test", "integration", "-v"], cwd=collection_dir, capture_output=True
	)  # pylint: disable=subprocess-run-check
	output(result.stdout)
	output(result.stderr)
	if result.returncode != 0:
		exit(result.returncode)
	input(collection_dir)


if __name__ == "__main__":
	integration_test()
