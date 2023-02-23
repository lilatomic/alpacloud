# python_sources(
# 	name="root",
# )

python_requirements(
	name="reqs0",
	module_mapping={
		"ansible-core": ["ansible"],
	},
	resolve=parametrize("tools", "ansible.lilatomic.azcli", "ansible.lilatomic.api"),
)

python_distribution(
	name="alpacloud",
	dependencies=[
		"tools/ansible_builder:alpacloud-ansible-builder",
	],
	provides=python_artifact(
		name="alpacloud",
		version="0.1.1",
		author="lilatomic",
		description="Metapackage for all my alpacloud tools",
		url="https://github.com/lilatomic/alpacloud",
		keywords=["metapackage"],
		long_description_content_type="text/markdown",
	),
	long_description_path="readme.md",
)
