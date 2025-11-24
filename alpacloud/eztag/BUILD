python_sources()

python_tests(
	name="tests",
	# dependencies=["./test_resources:k8s_objs"],
)

python_test_utils(
	name="test_utils",
)

python_distribution(
	name="alpacloud.eztag",
	repositories=["@alpacloud.eztag"],
	dependencies=[":eztag"],
	long_description_path="alpacloud/eztag/readme.md",
	provides=python_artifact(
		name="alpacloud_eztag",
		version="0.1.0",
		description="A library for filtering things based on tags",
		author="Daniel Goldman",
		classifiers=[
			"Development Status :: 3 - Alpha",
			"Programming Language :: Python :: 3.10",
			"Programming Language :: Python :: 3.11",
			"Programming Language :: Python :: 3.12",
			"Programming Language :: Python :: 3.13",
			"Programming Language :: Python :: 3.14",
			"Topic :: Utilities",
			"Topic :: System :: Systems Administration",
		],
		license="Round Robin 2.0.0",
		long_description_content_type="text/markdown",
	),
)
