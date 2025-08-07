python_sources()

python_tests(
	name="tests",
	dependencies=["./test_resources:k8s_objs", "//:reqs1#pytest-asyncio"],
)

python_distribution(
	name="alpacloud.crdvis",
	repositories=["@alpacloud.crdvis"],
	dependencies=[":crdvis"],
	long_description_path="alpacloud/crdvis/readme.md",
	provides=python_artifact(
		name="alpacloud.crdvis",
		version="0.1.0",
		description="A visualiser for Kubernetes CRDs",
		author="Daniel Goldman",
		entry_points={"console_scripts": ["crdvis=alpacloud.crdvis:run_crdvis"]},
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
