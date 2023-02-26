from __future__ import annotations

import io
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class AnsibleTaskResult(Enum):
	SUCCESS = "SUCCESS"
	FAILED = "FAILED!"


@dataclass
class AnsibleTaskOutput:
	host: str
	result: AnsibleTaskResult
	body: dict

	@classmethod
	def parse_ansible_output(cls, line: str) -> Optional[AnsibleTaskOutput]:
		if "|" in line and "=>" in line:
			host_sep = line.index("|")
			result_sep = line.index("=>")
			host = line[0:host_sep].strip()
			result = AnsibleTaskResult(line[host_sep + 1 : result_sep].strip())
			body = json.loads(line[result_sep + 2 :].strip())
			return AnsibleTaskOutput(host, result, body)
		return None


output_file = "ansible_output.json"


def run_ansible_playbook(playbook_path: str) -> List[AnsibleTaskOutput]:
	"""Run an Ansible playbook and capture output"""
	os.environ["ANSIBLE_STDOUT_CALLBACK"] = "oneline"
	os.environ["ANSIBLE_COLLECTIONS_PATHS"] = ":".join(["."])
	os.environ[
		"ANSIBLE_LOG_PATH"
	] = output_file  # forces logging, even though it doesn't actually go here

	subprocess.run(["ansible-galaxy", "collection", "list"])

	# need to import here, after setting environemnt variables,
	# because Ansible doesn't really do the dependency-injection thing
	import ansible.cli.playbook as pb

	logger = logging.getLogger("ansible")
	stream = io.StringIO()
	handler = logging.StreamHandler(stream)
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)

	pb.PlaybookCLI(
		[
			"",
			playbook_path,
		]
	).run()

	lines = stream.getvalue().split("\n")
	results = list(filter(None, map(AnsibleTaskOutput.parse_ansible_output, lines)))
	return results


def test_integration__cli():
	results = run_ansible_playbook(
		"ansible_collections/lilatomic/azcli/tests/integration/targets/action_cli/tasks/main.yml"
	)
	assert results
	assert [r.result for r in results] == [
		AnsibleTaskResult.SUCCESS,
		AnsibleTaskResult.SUCCESS,
		AnsibleTaskResult.SUCCESS,
		AnsibleTaskResult.FAILED,
		AnsibleTaskResult.SUCCESS,
		AnsibleTaskResult.FAILED,
		AnsibleTaskResult.SUCCESS,
	]
