from ansible_it.ansible_it import AnsibleTaskResult, run_ansible_playbook


def test_inegration__api__main():
	results = run_ansible_playbook(
		"ansible_collections/lilatomic/api/tests/integration/targets/http/tasks/main.yml"
	)
	assert [r.result for r in results] == [AnsibleTaskResult.SUCCESS] * 4


def test_integration__performance__api():
	results = run_ansible_playbook(
		"ansible_collections/lilatomic/api/tests/integration/targets/http/tasks/performance_api.yml"
	)
	assert [r.result for r in results] == [AnsibleTaskResult.SUCCESS]


def test_integration__performance__uri():
	results = run_ansible_playbook(
		"ansible_collections/lilatomic/api/tests/integration/targets/http/tasks/performance_uri.yml"
	)
	assert [r.result for r in results] == [AnsibleTaskResult.SUCCESS]
