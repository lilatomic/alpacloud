python_sources(sources=["plugins/**/*.py"])

python_tests(
	name="tests",
	sources=["tests/**/test_*.py"],
)

python_requirements(
	name="reqs",
	module_mapping={
		"azure-cli": ["azure.cli"],
	},
)
