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

debounce = datetime.timedelta(seconds=1)


@click.command()
@click.argument("dirs", nargs=-1)
@click.option("--watch", is_flag=True)
def launch(dirs, watch):
	def install_all():
		log.msg("init", dir_count=len(dirs))
		for d in dirs:
			install(d)

	if watch:

		to_process = {}

		def handle_change(event):
			segments = event.src_path.split("/")
			path = os.path.join(*segments[:3])
			to_process[path] = datetime.datetime.now()

		handler = PatternMatchingEventHandler(
			patterns="*", ignore_patterns="", ignore_directories=False, case_sensitive=True
		)
		handler.on_any_event = handle_change

		my_observer = Observer()
		for d in dirs:
			my_observer.schedule(handler, path=d, recursive=True)

		my_observer.start()
		log.msg("observation", op="start", dir_count=len(dirs))
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


def install(directory):
	log.msg("installing", collection=directory)

	r = subprocess.run(
		f"ansible-galaxy collection build {directory} --output-path build/{directory} --force",
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)
	log.msg("installing", op="build", stdout=r.stdout, stderr=r.stderr)
	r = subprocess.run(
		f"ansible-galaxy collection install --force build/{directory}/*",
		shell=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)
	log.msg("installing", op="install", stdout=r.stdout, stderr=r.stderr)


if __name__ == "__main__":
	launch()
