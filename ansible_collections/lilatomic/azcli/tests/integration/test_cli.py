from __future__ import annotations

from ansible_it.ansible_it import AnsibleTaskResult, run_ansible_playbook


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
