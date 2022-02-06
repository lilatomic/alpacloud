python_requirements()

resources(
	name="build_resources",
	sources=["pyproject.toml","readme.md","MANIFEST.in"],
)

python_sources(name="ansible_builder_src")

python_distribution(
	name="alpacloud-ansible-builder",
	dependencies=[
		":build_resources",
		":ansible_builder_src"
	],
	provides=python_artifact(
		name="alpacloud_ansible_builder",
		version="0.1.3",
	),
	generate_setup = False,
)
