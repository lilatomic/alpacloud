python_sources()

python_tests(
	name="tests",
	dependencies=["./test_resources:k8s_objs"],
)

python_test_utils(
	name="test_utils",
)

python_distribution(
	name="alpacloud.lens",
	repositories=["@alpacloud.lens"],
	dependencies=[":lens", ":py.typed"],
	long_description_path="alpacloud/lens/readme.md",
	provides=python_artifact(
		name="alpacloud.lens",
		version="0.1.0",
		description="A library for modifying Kubernetes manifests and other json-like objects.",
		author="Daniel Goldman",
		classifiers=[
			"Development Status :: 3 - Alpha",
			"Programming Language :: Python :: 3.10",
			"Programming Language :: Python :: 3.11",
			"Programming Language :: Python :: 3.12",
			"Programming Language :: Python :: 3.13",
			"Topic :: Utilities",
			"Topic :: System :: Systems Administration",
		],
		license="Round Robin 2.0.0",
		long_description_content_type="text/markdown",
	),
)

resource(name="py.typed", source="py.typed")
