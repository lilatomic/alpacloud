python_sources(
	sources=["plugins/**/*.py"],
	resolve="ansible.lilatomic.azcli",
)

files(name="ansible_playbooks", sources=["tests/integration/**/*.yml"])

python_tests(
	name="tests",
	sources=["tests/unit/test_*.py"],
	resolve="ansible.lilatomic.azcli",
)

python_tests(
	name="integration",
	sources=["tests/integration/test_*.py"],
	resolve="ansible.lilatomic.azcli",
	dependencies=[":ansible_playbooks", ":reqs", ":azcli"],
	tags=["integration"],
)

python_requirements(
	name="reqs",
	module_mapping={
		"azure-cli": ["azure.cli"],
		"ansible-core": ["ansible"],
	},
	resolve="ansible.lilatomic.azcli",
)
