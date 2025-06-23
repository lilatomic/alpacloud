import dataclasses
from dataclasses import dataclass
from typing import Callable, Optional

from alpacloud.lens.models import CombinedLens, kord, CodecLens, C, B, A, BoundLens, CodecLensABC, F, korl, FilterLens

metadata = kord("metadata")
namespace = metadata["namespace"]
name = metadata["name"]
annotation = metadata / kord("annotations")
labels = metadata / kord("labels")


deployment_labels = CombinedLens(
	(
		kord("spec") / kord("selector") / kord("matchLabels"),
		kord("spec") / kord("template") / labels,
	)
)

def xdict(extensions: dict) -> Callable[[dict], dict]:
	def _xdict(d: dict) -> dict:
		return {**d, **extensions}
	return _xdict


@dataclass
class Image:
	registry: str
	repository: str
	tag: str = "latest"
	digest: Optional[str] = None

def decode_image(image_str: str) -> Image:
	""""""
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
	name = "ImageCodec"

	def dec(self, a: A) -> C:
		return decode_image(a)

	def enc(self, c: C) -> B:
		return encode_image(c)

	@staticmethod
	def set_registry(registry: str) -> F:
		return lambda i: dataclasses.replace(i, tag=registry)

	@staticmethod
	def set_repository(repository: str) -> F:
		return lambda i: dataclasses.replace(i, repository=repository)

	@staticmethod
	def set_tag(tag: str) -> F:
		return lambda i: dataclasses.replace(i, tag=tag)

	@staticmethod
	def set_digest(digest: str) -> F:
		return lambda i: dataclasses.replace(i, digest=digest)


containers = kord("spec") / korl("containers")


def image(container_name: str):
	return containers * FilterLens(lambda container: container["name"] == container_name, predicate_name=f'name=={container_name}')["image"]
