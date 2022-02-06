python_requirements()

resource(name="pyproject", source="pyproject.toml")
resource(name="readme", source="readme.md")
resource(name="manifest", source="MANIFEST.in")

python_sources(name="ansible_builder_src")


python_distribution(
	name="alpacloud-ansible-builder",
	dependencies=[
		":pyproject",
		":readme",
		":manifest",
		":ansible_builder_src"
		# ""
	],
	provides=python_artifact(
		name="alpacloud_ansible_builder",
		version="0.1.3",
	),
	generate_setup = False,
)
