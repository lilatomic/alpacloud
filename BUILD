# python_sources(
# 	name="root",
# )

python_requirements(
	name="reqs0",
	module_mapping={
		"ansible-core": ["ansible"],
		"pyyaml": ["yaml"],
	},
	resolve=parametrize("tools", "ansible.lilatomic.azcli", "ansible.lilatomic.api"),
	source="requirements_global.txt",
)

python_requirements(
	name="reqs1",
	resolve="tools",
	source="requirements.txt",
)

python_requirement(
	requirements=["mypy~=1.16.1", "types-PyYAML", "types-requests"],
	resolve="tools",
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
