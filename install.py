#!/usr/bin/env python3

import subprocess

import click


@click.command()
@click.argument("dirs", nargs=-1)
@click.option("--watch", is_flag=True)
def launch(dirs, watch):
	print(dirs)
	for d in dirs:
		install(d)


def install(directory):
	r = subprocess.run(
		f"ansible-galaxy collection build {directory} --output-path build/{directory} --force",
		shell=True,
	)
	print(r.stdout)
	print(r.stdout)
	r = subprocess.run(
		f"ansible-galaxy collection install --force build/{directory}/*", shell=True
	)
	print(r.stdout)
	print(r.stdout)


if __name__ == "__main__":
	launch()
