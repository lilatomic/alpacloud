python_sources(sources=["plugins/**/*.py"])

python_tests(
	name="tests",
	sources=["tests/**/test_*.py"],
	resolve="ansible.lilatomic.azcli",
)

python_requirements(
	name="reqs",
	module_mapping={
		"azure-cli": ["azure.cli"],
		"ansible-core": ["ansible"],
	},
	resolve="ansible.lilatomic.azcli",
)
