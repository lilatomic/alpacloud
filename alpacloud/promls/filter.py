"""Filter metrics."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable

from alpacloud.promls.metrics import Metric

Predicate = Callable[[Metric], bool]
PredicateFactory = Callable[[str], Predicate]
EPSILON = 1e-3
l = logging.getLogger(__name__)


@dataclass
class MetricsTree:
	"""A tree of metrics."""

	metrics: dict[str, Metric]

	@classmethod
	def mk_tree(cls, metrics: list[Metric]) -> MetricsTree:
		"""
		Construct a metrics tree from a list of metrics.
		"""
		return cls(
			{e.name: e for e in metrics},
		)

	def filter(self, predicate: Predicate) -> MetricsTree:
		"""Filter this metrics tree."""
		return MetricsTree({k: v for k, v in self.metrics.items() if predicate(v)})


def filter_name(pattern: re.Pattern) -> Predicate:
	"""Filter metrics for name"""

	def predicate(metric: Metric) -> bool:
		return pattern.search(metric.name) is not None

	return predicate


def filter_any(pattern: re.Pattern) -> Predicate:
	"""Filter metrics for any field"""

	def _match_label_set(labels: dict[str, str]) -> bool:
		return any(pattern.search(k) or pattern.search(v) for k, v in labels.items())

	def predicate(metric: Metric) -> bool:
		return pattern.search(metric.name) is not None or pattern.search(metric.help) is not None or any(_match_label_set(labels) for labels in metric.labels)

	return predicate


def filter_path(path: list[str]) -> Predicate:
	"""Filter metrics for path components."""
	pattern = re.compile("^" + "_".join(path))

	def predicate(metric: Metric) -> bool:
		return pattern.match(metric.name) is not None

	return predicate
