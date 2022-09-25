#!/usr/bin/env python
import os.path
import subprocess
import shutil
from tempfile import TemporaryDirectory


def output(b: bytes) -> None:
	o = b.decode('utf-8').replace("\\n", "\n")
	print(o)


def integration_test():
	test_dir = TemporaryDirectory()

	collection_root_dir = os.path.join(test_dir.name, "ansible_collections")
	collection_dir = os.path.join(collection_root_dir, "lilatomic/azcli")
	shutil.copytree("lilatomic/azcli", collection_dir)
	result = subprocess.run(["ansible-test", "integration", "-v"], cwd=collection_dir, capture_output=True)
	output(result.stdout)
	output(result.stderr)
	if result.returncode != 0:
		exit(result.returncode)
	input(collection_dir)


if __name__ == "__main__":
	integration_test()
