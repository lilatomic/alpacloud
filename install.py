#!/usr/bin/env python3

import os
import subprocess
import datetime
import time
from structlog import get_logger

import click
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


log = get_logger()


@click.command()
@click.argument("roots", nargs=-1)
@click.option("--watch", is_flag=True)
@click.option(
	"--debounce", default=1000, help="time to wait for last modification, in ms"
)
def launch(roots, watch, debounce):
	debounce = datetime.timedelta(milliseconds=debounce)

	collections = flat_map(find_collections, roots)
	log.msg("collections found", collections=collections)

	def install_all():
		log.msg("init", dir_count=len(collections))
		for c in collections:
			install(c)

	if watch:

		to_process = {}

		def handle_change(event):
			event_path = event.src_path
			collection = next((x for x in collections if event_path.startswith(x)))

			log.msg("change event", trigger=event.src_path, collection_path=collection)
			to_process[collection] = datetime.datetime.now()

		handler = PatternMatchingEventHandler(
			patterns="*", ignore_patterns="", ignore_directories=False, case_sensitive=True
		)
		handler.on_any_event = handle_change

		my_observer = Observer()
		for d in collections:
			my_observer.schedule(handler, path=d, recursive=True)

		my_observer.start()
		log.msg("observation", op="start", dir_count=len(roots))
		try:
			while True:
				time.sleep(1)
				now = datetime.datetime.now()
				to_remove = []
				for k, v in to_process.copy().items():
					if now > v + debounce:
						install(k)
						to_remove.append(k)
				for k in to_remove:
					del to_process[k]

		except KeyboardInterrupt:
			log.msg("observation", op="stop")
			my_observer.stop()
			my_observer.join()
	else:
		install_all()


def find_collections(root):
	s = set()
	for path, _dirs, files in os.walk(root):
		if "galaxy.yml" in files:
			s.add(path)
	return s


def install(directory):
	log.msg("installing", collection=directory)

	output_dir = f"build/{directory}"

	r = subprocess.run(
		f"ansible-galaxy collection build {directory} --output-path {output_dir} --force",
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)
	log.msg("installing", op="build", stdout=r.stdout, stderr=r.stderr)
	r = subprocess.run(
		f"ansible-galaxy collection install --force {output_dir}/*",
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)
	log.msg("installing", op="install", stdout=r.stdout, stderr=r.stderr)


def flat_map(f, xs):
	ys = []
	for x in xs:
		ys.extend(f(x))
	return ys


if __name__ == "__main__":
	launch()