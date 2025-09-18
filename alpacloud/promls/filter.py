from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from alpacloud.promls.metrics import Metric

Predicate = Callable[[Metric], bool]


@dataclass
class MetricsTree:
	metrics: dict[str, Metric]

	@classmethod
	def mk_tree(cls, metrics: list[Metric]) -> MetricsTree:
		return cls(
			{e.name: e for e in metrics},
		)

	def filter(self, predicate: Predicate) -> MetricsTree:
		return MetricsTree({k: v for k, v in self.metrics.items() if predicate(v)})


def filter_name(pattern: re.Pattern) -> Predicate:
	def predicate(metric: Metric) -> bool:
		return pattern.search(metric.name) is not None

	return predicate


def filter_any(pattern: re.Pattern) -> Predicate:
	def predicate(metric: Metric) -> bool:
		return pattern.search(metric.name) is not None or pattern.search(metric.help) is not None

	return predicate


def filter_path(path: list[str]) -> Predicate:
	pattern = re.compile("^" + "_".join(path))

	def predicate(metric: Metric) -> bool:
		return pattern.match(metric.name) is not None

	return predicate
