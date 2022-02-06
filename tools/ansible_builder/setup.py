"""Setup alpacloud-ansible-builder"""
from setuptools import setup

with open("readme.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setup(
	name="alpacloud-ansible-builder",
	version="0.1.3",
	author="lilatomic",

	py_modules=["alpacloud_ansible_builder"],
	install_requires=[
		"click>=7,<9",
		"structlog~=21.1",
		"watchdog~=2.0",
		"pyyaml~=6.0",
	],
	entry_points="""
	[console_scripts]
	alpacloud-ansible-builder=alpacloud_ansible_builder:launch
	""",
	description="This tool automatically builds and installs Ansible Collections",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/lilatomic/alpacloud",
	project_urls={
		"Bug Tracker": "https://github.com/lilatomic/alpacloud/issues"
	},
	package_data={
		"": ["*.md"]
	}
)
