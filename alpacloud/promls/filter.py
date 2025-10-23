from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable

from alpacloud.promls.metrics import Metric

Predicate = Callable[[Metric], bool]
EPSILON = 1e-3
l = logging.getLogger(__name__)


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
		mismatch = letter_mismatch(metric.name, pattern)
		if mismatch > len(pattern) / 2:
			l.debug(f"{metric.name} letter mismatch too high: {mismatch}")
			return False
		distance = query_levenshtein(metric.name, pattern, 0, 0, (len(metric.name) + len(pattern)) / 4, False)
		ratio = distance / len(pattern)
		allowable_distance = max(0.1, 1 / len(pattern))  # 10% of the length of the pattern or 1 character
		val = ratio - allowable_distance < EPSILON
		l.debug(f"{metric.name} ratio: {ratio}, allowable_distance: {allowable_distance}, val: {val}")
		return val  # epsilon comparison for floating point inexactness`

	return predicate


def letter_mismatch(s, q):
	"""Quickly eliminate metrics that will never match."""

	def letter_dict(v: str) -> dict[str, int]:
		d = {}
		for c in v:
			d[c] = d.get(c, 0) + 1
		return d

	s = letter_dict(s)
	q = letter_dict(q)

	misses = 0
	for k, v in q.items():
		delta = v - s.get(k, 0)
		if delta > 0:
			misses += abs(delta)

	return misses


def query_levenshtein(s, q, si, qi, badness: float, started):
	"""
	Modified Levenshtein distance.
	Tries to not impose penalties for substring matches:
	- do not penalise advancing
	- do not penalise differences after a complete match

	args:
	- si: start index of s
	- qi: start index of q
	"""
	if badness <= 0:
		return 1e6
	if len(s) == si:  # unprocessed query
		return len(q)
	elif len(q) == qi:  # entire query is processed, so we're happy
		return 0
	elif s[si] == q[qi]:
		return query_levenshtein(s, q, si + 1, qi + 1, badness, True)
	else:
		skip_s = query_levenshtein(s, q, si + 1, qi, badness - 1, started)
		return min(
			skip_s + 1 if started else skip_s,
			1 + query_levenshtein(s, q, si, qi + 1, badness - 1, True),
			1 + query_levenshtein(s, q, si + 1, qi + 1, badness - 1, True),
		)
