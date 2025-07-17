python_sources()

docker_image(
	name="docker",
	registries=["ghcr.io/lilatomic"],
	repository="alpacloud/cmp",
	image_tags=["0.0.1", env("tgttag", "localtest")],
)

python_tests(
	name="tests",
	dependencies=["./test_resources:k8s_objs"],
	runtime_package_dependencies=["./test_resources:my_postrenderer"],
)

pex_binary(
	name="__main__",
	entry_point="__main__.py",
	interpreter_constraints=["CPython==3.13.*"],
)

python_distribution(
	name="alpacloud.argocdkit",
	repositories=["@alpacloud.argocdkit"],
	dependencies=[":argocdkit"],
	long_description_path="alpacloud/argocdkit/readme.md",
	provides=python_artifact(
		name="alpacloud.argocdkit",
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
	),
)
