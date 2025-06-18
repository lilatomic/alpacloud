from dataclasses import dataclass
from typing import Callable, Optional

from alpacloud.lens.models import CombinedLens, kord, CodecLens

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

	# Split by last colon to separate tag (not port!)
	if '@' in image_str:
		image_str, _ = image_str.split('@', 1)  # ignore digest for this case

	parts = image_str.rsplit(':', 1)
	if len(parts) == 2 and '/' in parts[0] or '.' in parts[0] or ':' in parts[0]:
		# ':' before tag and '/' or '.' implies tag
		image_body, tag = parts
	else:
		image_body = image_str
		tag = default_tag

	# Split registry and repo
	segments = image_body.split('/')
	if len(segments) == 1:
		registry = default_registry
		repository = segments[0]
	elif '.' in segments[0] or ':' in segments[0] or segments[0] == 'localhost':
		# first part is registry
		registry = segments[0]
		repository = '/'.join(segments[1:])
	else:
		registry = default_registry
		repository = image_body

	return Image(registry=registry, repository=repository, tag=tag)

def encode_image(image: Image) -> str:
	"""
	Serialize an Image instance back to a Docker image string.
	"""
	parts = []
	if image.registry != "docker.io":
		parts.append(image.registry)
	parts.append(image.repository)
	return f"{'/'.join(parts)}:{image.tag}"
