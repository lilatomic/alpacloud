"""Lenses for working with Kubernetes objects"""

from __future__ import annotations

import base64
import dataclasses
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Pattern

from alpacloud.lens.models import (
	BoundLensT,
	CodecLensABC,
	CombinedBoundLens,
	CombinedLens,
	Const,
	DataclassCodec,
	FilterLens,
	IndexLens,
	KeyLens,
	Lens,
	LensT,
	append,
	kord,
	korl,
)
from alpacloud.lens.util.type import JSONT, B, F

metadata = kord("metadata")
namespace = metadata["namespace"]
name = metadata["name"]
annotation = metadata / kord("annotations")
labels = metadata / kord("labels")

spec = kord("spec")
deployment_labels = CombinedLens(
	(
		spec / kord("selector") / kord("matchLabels"),
		spec / kord("template") / labels,
	)
)


def xdict(extensions: dict) -> Callable[[dict], dict]:
	"""Extend a dictionary"""

	def _xdict(d: dict) -> dict:
		return {**d, **extensions}

	return _xdict


@dataclass
class Image:
	"""A Docker image reference"""

	registry: str
	repository: str
	tag: str = "latest"
	digest: Optional[str] = None


def decode_image(image_str: str) -> Image:
	"""Load a Docker image from the `image` string."""
	# Default values
	default_registry = "docker.io"
	default_tag = "latest"

	if "@" in image_str:
		without_digest, digest = image_str.split("@", 1)
	else:
		digest = None
		without_digest = image_str

	match without_digest.split("/", 1):
		case [maybe_registry, maybe_unbound_image]:
			if "." in maybe_registry or "localhost" in maybe_registry:
				# registry needs to be a valid domain name,
				# so if it exists it will have a "." or be "localhost"
				registry = maybe_registry
				unbound_image = maybe_unbound_image
			else:
				# does not have a registry
				registry = default_registry
				unbound_image = without_digest
		case [maybe_unbound_image]:
			registry = default_registry
			unbound_image = maybe_unbound_image
		case _:
			raise TypeError(f"Unknown image format: {image_str}")

	match unbound_image.split(":"):
		case [repository, tag]:
			return Image(registry, repository, tag, digest)
		case [repository]:
			return Image(registry, repository, default_tag, digest)
		case _:
			raise ValueError(f"Invalid image format, too many colons image={without_digest}")


def encode_image(image: Image) -> str:
	"""
	Serialize an Image instance back to a Docker image string.
	"""
	out = ""
	if image.registry:
		out += image.registry + "/"
	out += image.repository
	if image.tag:
		out += ":" + image.tag
	if image.digest:
		out += "@" + image.digest
	return out


class ImageCodec(CodecLensABC):
	"""Lens to transform the `image` property of a Kubernetes manifest into a dataclass"""

	@property
	def l_name(self) -> str:
		return super()._fmt_name("ImageCodec")

	def dec(self, a: str) -> Image:
		return decode_image(a)

	def enc(self, c: Image) -> str:
		return encode_image(c)

	@staticmethod
	def set_registry(registry: str) -> F:
		"""Set the registry of the image"""
		return lambda i: dataclasses.replace(i, registry=registry)

	@staticmethod
	def set_repository(repository: str) -> F:
		"""Set the repository of the image."""
		return lambda i: dataclasses.replace(i, repository=repository)

	@staticmethod
	def set_tag(tag: str) -> F:
		"""Set the tag of the image."""
		return lambda i: dataclasses.replace(i, tag=tag)

	@staticmethod
	def set_digest(digest: str) -> F:
		"""Set the digest of the image."""
		return lambda i: dataclasses.replace(i, digest=digest)


containers = spec / korl("containers")


def container_named(container_name: str) -> FilterLens:
	"""Find a container with a specific name."""
	return FilterLens(lambda container: container["name"] == container_name, predicate_name=f"name=={container_name}")


def image(container_name: str):
	"""Get the image from a pod manifest."""
	return containers * container_named(container_name)["image"] / ImageCodec()


volumes = spec / korl("volumes")


def container_finder(container: str | int = 0):
	"""Find a container with a name or index from the list of containers."""
	if isinstance(container, int):
		return IndexLens(container)
	else:
		return container_named(container)


def add_volume(volume_name: str, volume: Any, container: str | int = 0, mount_path: str | None = None) -> BoundLensT:
	"""Add a volume to a pod."""
	if mount_path is None:
		mount_path = volume_name

	return CombinedBoundLens(
		(
			volumes @ append({"name": volume_name, **volume}),
			(containers / container_finder(container) / korl("volumeMounts")) @ append({"name": volume_name, "mountPath": mount_path}),
		)
	)


@dataclass
class NamedListCodec(CodecLensABC):
	"""Some lists have items with unique keys. This converts one of those lists into a dict"""

	n: str = "name"

	@property
	def l_name(self) -> str:
		return "indexable_list"

	def dec(self, a: list[dict]) -> dict[str, dict]:
		return {e[self.n]: e for e in a}

	def enc(self, c: dict[str, B]) -> list[B]:
		return list(c.values())


@dataclass
class Envvar:
	"""An envvar for a Kubernetes pod"""

	name: str
	value: str | None = None

	@staticmethod
	def set(v: str):
		"""Set the value of the envvar"""

		def _set_value(s: Envvar) -> Envvar:
			return Envvar(s.name, v)

		return _set_value


def envvar(n: str, container: str | int = 0) -> LensT:
	"""Lens to get an envvar of a container of a pod."""
	return containers / container_finder(container) / korl("env") / NamedListCodec() / KeyLens(n, {"name": n}) / DataclassCodec(Envvar)


def set_host(host: str) -> BoundLensT:
	"""Set all hosts to the same root domain"""

	return CombinedBoundLens(((spec["rules"] * KeyLens("host")) @ Const(host), (spec / kord("tls") * korl("hosts")) @ Const([host])))


def replace_root_domain(old_root, new_root) -> Callable[[str], str]:
	def _replace_root_domain(s: str) -> str:
		return s.replace(old_root, new_root)

	return _replace_root_domain


def mut_hosts(f: Callable[[str], str]) -> BoundLensT:
	"""modify all hosts in an ingress"""

	return CombinedBoundLens(((spec["rules"] * KeyLens("host", None)) @ f, (spec / kord("tls") * korl("hosts") * Lens()) @ f))


class B64(CodecLensABC):
	@property
	def l_name(self) -> str:
		return super()._fmt_name("base64")

	def dec(self, a: str) -> str:
		return base64.b64decode(a.encode()).decode()

	def enc(self, c: str) -> str:
		return base64.b64encode(c.encode()).decode()


def Item(kind: str, name: str | Pattern = re.compile(r".*")) -> FilterLens:
	if isinstance(name, str):
		name = re.compile(name)

	def matches(e: JSONT) -> bool:
		return (
			KeyLens("kind").l_get(e).lower() == kind.lower()  # type: ignore
			and bool(name.fullmatch(metadata["name"].l_get(e)))  # type: ignore
		)

	return FilterLens(
		predicate=matches,
		predicate_name=f'?(kind="{kind}", name=r"{name}")',
	)
