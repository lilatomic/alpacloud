"""Definitions for Prometheus metrics."""

from dataclasses import dataclass


@dataclass
class Metric:
	"""Base class for Prometheus metrics."""

	name: str
	help: str
	type: str
	labels: list[dict[str, str]]
