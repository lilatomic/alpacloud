python_sources(
	sources=["plugins/**/*.py"],
	resolve="ansible.lilatomic.api",
)

files(name="ansible_playbooks", sources=["tests/integration/**/*.yml"])

python_tests(
	name="integration",
	sources=["tests/integration/test_*.py"],
	resolve="ansible.lilatomic.api",
	dependencies=[":ansible_playbooks", ":reqs", ":api"],
	tags=["integration"],
)

python_requirements(
	name="reqs",
	module_mapping={"ansible-core": ["ansible"]},
	resolve="ansible.lilatomic.api",
)
