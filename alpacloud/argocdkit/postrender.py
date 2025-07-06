"""Helper for parsing and dumping Kubernetes manifests."""

from __future__ import annotations

import sys
from typing import Callable, TypeAlias

import yaml

from alpacloud.lens.models import BoundLensT
from alpacloud.lens.util.type import JSONT


class YamlDumper(yaml.SafeDumper):
	"""Safely dump YAML"""

	def ignore_aliases(self, data):
		return True

	@staticmethod
	def _str_presenter(dumper, data):
		"""Preserve multiline strings when dumping YAML"""
		if "\n" in data:
			# Remove any trailing spaces messing out the output.
			block = "\n".join([line.rstrip() for line in data.splitlines()])
			if data.endswith("\n"):
				block += "\n"
			return dumper.represent_scalar("tag:yaml.org,2002:str", block, style="|")
		return dumper.represent_scalar("tag:yaml.org,2002:str", data)

	@classmethod
	def safe_dump(cls, data, stream=None, **kwds):
		"""
		Serialize a Python object into a YAML stream.
		Produce only basic YAML tags.
		If stream is None, return the produced string instead
		"""
		return yaml.dump([data], stream, Dumper=cls, explicit_start=True, **kwds)

	@classmethod
	def safe_dump_all(cls, documents, stream=None, **kwds):
		"""
		Serialize a Python object into a YAML stream.
		Produce only basic YAML tags.
		If stream is None, return the produced string instead
		"""
		return yaml.dump_all(documents, stream, Dumper=cls, explicit_start=True, **kwds)

	@classmethod
	def safe_load_all(cls, stream):
		"""
		Load a multi-document YAML stream.

		Removes empty documents which sometimes appear.
		"""
		return [e for e in yaml.safe_load_all(stream) if e]


YamlDumper.add_representer(str, YamlDumper._str_presenter)
PostRenderer: TypeAlias = Callable[[], None]


def postrenderer_function(f: Callable[[list[JSONT]], list[JSONT]]) -> PostRenderer:
	"""Convert a function into a Helm postrenderer."""

	def _postrender():
		manifests = YamlDumper.safe_load_all(sys.stdin)
		transformed = f(manifests)
		YamlDumper.safe_dump_all(transformed, sys.stdout)

	return _postrender


def postrenderer_boundlens(f: BoundLensT) -> PostRenderer:
	"""Convert a BoundLens into a Helm postrenderer."""

	def _postrender():
		manifests = YamlDumper.safe_load_all(sys.stdin)
		transformed = f.map(manifests)
		YamlDumper.safe_dump_all(transformed, sys.stdout)

	return _postrender


def postrenderer(f: BoundLensT | Callable[[list[JSONT]], list[JSONT]]) -> PostRenderer:
	"""Convert things into a Helm postrenderer."""
	if isinstance(f, BoundLensT):
		return postrenderer_boundlens(f)
	elif callable(f):
		return postrenderer_function(f)
	else:
		raise TypeError("f must be BoundLensT or Callable")
