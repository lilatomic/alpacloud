from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from alpacloud.promls.metrics import Metric

Predicate = Callable[[Metric], bool]
EPSILON = 1e-3


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


def filter_ish(pattern: str) -> Predicate:
	"""
	Filter metrics for this that are kindof like what you want.
	Uses difflib
	"""

	def predicate(metric: Metric) -> bool:
		distance = query_levenshtein(metric.name, pattern, False)
		ratio = distance / len(pattern)
		allowable_distance = max(0.1, 1 / len(pattern))  # 10% of the length of the pattern or 1 character
		return ratio - allowable_distance < EPSILON  # epsilon comparison for floating point inexactness

	return predicate


def query_levenshtein(s, query, started):
	"""
	Modified Levenshtein distance.
	Tries to not impose penalties for substring matches:
	- do not penalise advancing
	- do not penalise differences after a complete match
	"""
	if len(s) == 0:  # unprocessed query
		return len(query)
	elif len(query) == 0:  # entire query is processed, so we're happy
		return 0
	elif s[0] == query[0]:
		return query_levenshtein(s[1:], query[1:], True)
	else:
		skip_s = query_levenshtein(s[1:], query, started)
		if started:  # if we aren't started, don't penalize advancing
			skip_s += 1
		return min(
			skip_s,
			1 + query_levenshtein(s, query[1:], True),
			1 + query_levenshtein(s[1:], query[1:], True),
		)
