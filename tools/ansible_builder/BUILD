python_requirements()

resource(name="pyproject", source="pyproject.toml")

#python_distribution(
#	name="alpacloud-ansible-builder",
#	dependencies=[
#		":pyproject"
#	],
#	provides=python_artifact(
#		name="alpacloud_ansible_builder",
#		version="0.1.3",
#	),
#	generate_setup = False,
#)

python_sources(name="ansible_builder_src")

pex_binary(
	name="alpacloud-ansible-builder",
	entry_point="alpacloud_ansible_builder.py:launch",
)