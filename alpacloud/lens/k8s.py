from typing import Callable

from alpacloud.lens.models import CombinedLens, kord

metadata = kord("metadata")
namespace = metadata["namespace"]
name = metadata["name"]
annotation = metadata % kord("annotations")
labels = metadata % kord("labels")


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