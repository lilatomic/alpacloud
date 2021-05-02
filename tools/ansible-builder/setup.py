from setuptools import setup

setup(
	name="alpacloud-ansible-builder",
	version="0.1.0",
	py_modules=["alpacloud_ansible_builder"],
	install_requires=[
		"ansible~=2.10.5",
		"click~=7.1.2",
		"structlog~=21.1.0",
		"watchdog~=2.0.2",
	],
	entry_points="""
	[console_scripts]
	alpacloud-ansible-builder=alpacloud_ansible_builder:launch
	""",
)
