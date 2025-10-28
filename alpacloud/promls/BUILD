python_sources(dependencies=[":css"])

resources(name="css", sources=["*.css"])

python_tests(
	name="tests",
	dependencies=["./test_resources:objs"],
)

python_distribution(
	name="alpacloud.promls",
	repositories=["@alpacloud.promls"],
	dependencies=[":promls"],
	long_description_path="alpacloud/promls/readme.md",
	provides=python_artifact(
		name="alpacloud.promls",
		version="0.1.0",
		description="A visualiser for available Prometheus metrics",
		author="Daniel Goldman",
		entry_points={"console_scripts": ["promls = alpacloud.promls.cli:search"]},
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
