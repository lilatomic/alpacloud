"""Setup Alpacloud metapackage"""
from setuptools import setup

with open("readme.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setup(
	name="alpacloud",
	version="0.1.1",
	author="lilatomic",

	description="Metapackage for all my alpacloud tools",
	long_description=long_description,


	url="https://github.com/lilatomic/alpacloud",

	install_requires=[
		"alpacloud-ansible-builder~=0.1.2"
	],
	keywords=[
		"metapackage"
	],
)
