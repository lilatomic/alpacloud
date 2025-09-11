from dataclasses import dataclass


@dataclass
class Metric:
	"""Base class for Prometheus metrics."""

	name: str
	help: str
	type: str
