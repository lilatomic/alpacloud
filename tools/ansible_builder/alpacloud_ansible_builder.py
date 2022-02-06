"""Install Ansible Collections automatically"""
from collections import namedtuple
from functools import reduce
import os
import subprocess
import datetime
import time
from typing import Dict, Iterator
import yaml
from structlog import get_logger

import click
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


log = get_logger()


Collection = namedtuple("Collection", ["namespace", "name", "version", "galaxy"])


@click.command()
@click.argument("roots", nargs=-1)
@click.option("--watch", is_flag=True)
@click.option(
	"--debounce", default=1000, help="time to wait for last modification, in ms"
)
def launch(roots, watch, debounce):
	"""Install Ansible Collections automatically"""
	debounce = datetime.timedelta(milliseconds=debounce)

	collections = collect_mappings(map(find_collections, roots))
	log.msg("collections found", collections=collections)

	def install_all():
		log.msg("init", dir_count=len(collections))
		for c in collections.items():
			install(*c)

	if watch:

		to_process = {}

		def handle_change(event):
			event_path = event.src_path
			path = next((path for path in collections.keys() if event_path.startswith(path)))

			log.msg("change event", trigger=event.src_path, collection_path=path)
			to_process[path] = datetime.datetime.now()

		handler = PatternMatchingEventHandler(
			patterns="*", ignore_patterns="", ignore_directories=False, case_sensitive=True
		)
		handler.on_any_event = handle_change

		my_observer = Observer()
		for d in collections.keys():
			my_observer.schedule(handler, path=d, recursive=True)

		my_observer.start()
		log.msg("observation", op="start", dir_count=len(collections))
		try:
			while True:
				time.sleep(1)
				now = datetime.datetime.now()
				to_remove = []
				for k, v in to_process.copy().items():
					if now > v + debounce:
						install(k, collections[k])
						to_remove.append(k)
				for k in to_remove:
					del to_process[k]

		except KeyboardInterrupt:
			log.msg("observation", op="stop")
			my_observer.stop()
			my_observer.join()
	else:
		install_all()


def collect_mappings(mappings: Iterator[Dict[str, Collection]]) -> Dict[str, Collection]:
	"""Flatten mappings"""
	return reduce(lambda a, b: {**a, **b}, mappings)


def find_collections(root) -> Dict[str, Collection]:
	"""Recursively traverses a directory and adds any directories with a galaxy.yml"""
	s = {}
	for path, _dirs, files in os.walk(root):
		if "galaxy.yml" in files:
			with open(os.path.join(path, "galaxy.yml"), encoding="utf-8") as f:
				galaxy = yaml.safe_load(f.read())

			galaxy_fields = {
				k: galaxy[k] for k in Collection._fields if k != "galaxy"
			}

			s[path] = Collection(
				**galaxy_fields, galaxy=galaxy
			)
	return s


def install(path: str, collection: Collection):
	"""Builds and installs an Ansible Collection"""
	log.msg("installing", collection=path)

	output_dir = os.path.join("build", collection.namespace, collection.name)
	built_collection_name = (
		f"{collection.namespace}-{collection.name}-{collection.version}.tar.gz"
	)

	try:
		r = subprocess.run(
			f"ansible-galaxy collection build --output-path {output_dir} --force {path}",
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			check=True,
		)
		log.msg("installing", op="build", stdout=r.stdout, stderr=r.stderr)
	except subprocess.CalledProcessError:
		log.exception("installing", op="build", exc_info=True)
		raise
	try:
		r = subprocess.run(
			f"ansible-galaxy collection install --force {output_dir}/{built_collection_name}",
			shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			check=True,
		)
		log.msg("installing", op="install", stdout=r.stdout, stderr=r.stderr)
	except subprocess.CalledProcessError:
		log.exception("installing", op="build", exc_info=True)
		raise
