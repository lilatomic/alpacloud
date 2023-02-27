"""Helpers for running Ansible integration tests"""

from __future__ import annotations

import io
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

output_file = "ansible_output.json"


class AnsibleTaskResult(Enum):
	"""Result string of running an Ansible task"""

	SUCCESS = "SUCCESS"
	FAILED = "FAILED!"


@dataclass
class AnsibleTaskOutput:
	"""Parsed output of running an Ansible task"""

	host: str
	result: AnsibleTaskResult
	body: dict

	@classmethod
	def parse_ansible_output(cls, line: str) -> Optional[AnsibleTaskOutput]:
		"""Parse an output line"""
		if "|" in line and "=>" in line:
			host_sep = line.index("|")
			result_sep = line.index("=>")
			host = line[0:host_sep].strip()
			result = AnsibleTaskResult(line[host_sep + 1 : result_sep].strip())
			body = json.loads(line[result_sep + 2 :].strip())
			return AnsibleTaskOutput(host, result, body)
		return None


def run_ansible_playbook(playbook_path: str) -> List[AnsibleTaskOutput]:
	"""Run an Ansible playbook and capture output"""
	os.environ["ANSIBLE_STDOUT_CALLBACK"] = "oneline"
	os.environ["ANSIBLE_COLLECTIONS_PATHS"] = ":".join(["."])
	os.environ[
		"ANSIBLE_LOG_PATH"
	] = output_file  # forces logging, even though it doesn't actually go here

	# need to import here, after setting environemnt variables,
	# because Ansible doesn't really do the dependency-injection thing
	# pylint: disable=import-outside-toplevel
	from ansible.executor.playbook_executor import PlaybookExecutor
	from ansible.inventory.manager import InventoryManager
	from ansible.parsing.dataloader import DataLoader
	from ansible.vars.manager import VariableManager

	logger = logging.getLogger("ansible")
	for handler in logger.handlers:
		logger.removeHandler(handler)
	stream = io.StringIO()
	handler = logging.StreamHandler(stream)
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)

	from ansible import context

	context.CLIARGS._store["syntax"] = False
	context.CLIARGS._store["start_at_task"] = None

	loader = DataLoader()
	inventory = InventoryManager(loader=loader)
	pbex = PlaybookExecutor(
		playbooks=[playbook_path],
		loader=loader,
		inventory=inventory,
		variable_manager=VariableManager(loader=loader, inventory=inventory),
		passwords={},
	)
	pbex.run()  # doesn't seem to return anything, but maybe it should?

	lines = stream.getvalue().split("\n")
	results = list(filter(None, map(AnsibleTaskOutput.parse_ansible_output, lines)))
	return results
