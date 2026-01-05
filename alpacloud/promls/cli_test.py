"""Tests for CLI functions."""
# pylint: disable=redefined-outer-name,

import json

import pytest

from alpacloud.promls.cli import PrintMode, do_print
from alpacloud.promls.filter import MetricsTree
from alpacloud.promls.metrics import Metric


@pytest.fixture
def test_metrics():
	"""Common test data for all PrintMode tests."""
	return [
		Metric(name="http_requests_total", help="Total HTTP requests", type="counter", labels=[]),
		Metric(name="http_requests_failed", help="Failed HTTP requests", type="counter", labels=[]),
		Metric(name="http_response_time_seconds", help="HTTP response time", type="histogram", labels=[]),
		Metric(name="database_connections_active", help="Active database connections", type="gauge", labels=[]),
		Metric(name="database_queries_total", help="Total database queries", type="counter", labels=[]),
	]


@pytest.fixture
def test_tree(test_metrics):
	"""Create a MetricsTree from test metrics."""
	return MetricsTree.mk_tree(test_metrics)


class TestPrintModeFlat:
	"""Tests for PrintMode.flat"""

	def test_flat_output_contains_all_metrics(self, test_tree, test_metrics):
		"""Test that flat mode contains all metric names."""
		result = do_print(test_tree, PrintMode.flat)

		for metric in test_metrics:
			assert metric.name in result

	def test_flat_output_contains_types(self, test_tree, test_metrics):
		"""Test that flat mode contains metric types."""
		result = do_print(test_tree, PrintMode.flat)

		for metric in test_metrics:
			assert metric.type in result

	def test_flat_output_contains_help(self, test_tree, test_metrics):
		"""Test that flat mode contains help text."""
		result = do_print(test_tree, PrintMode.flat)

		for metric in test_metrics:
			if metric.help:
				assert metric.help in result

	def test_flat_output_format(self, test_tree):
		"""Test that flat mode follows expected format."""
		result = do_print(test_tree, PrintMode.flat)
		lines = result.split("\n")

		# Should have one line per metric
		assert len(lines) == len(test_tree.metrics)

		# Each line should contain parentheses (for type)
		for line in lines:
			assert "(" in line and ")" in line

	def test_flat_empty_tree(self):
		"""Test flat mode with empty tree."""
		empty_tree = MetricsTree({})
		result = do_print(empty_tree, PrintMode.flat)
		assert result == ""

	def test_flat_metric_without_help(self):
		"""Test flat mode with metric without help text."""
		metric = Metric(name="test_metric", help="", type="counter", labels=[])
		tree = MetricsTree.mk_tree([metric])
		result = do_print(tree, PrintMode.flat)

		assert "test_metric" in result
		assert "(counter)" in result


class TestPrintModeFull:
	"""Tests for PrintMode.full"""

	def test_full_output_contains_help_comments(self, test_tree, test_metrics):
		"""Test that full mode contains HELP comments."""
		result = do_print(test_tree, PrintMode.full)

		for metric in test_metrics:
			assert f"# HELP {metric.name} {metric.help}" in result

	def test_full_output_contains_type_comments(self, test_tree, test_metrics):
		"""Test that full mode contains TYPE comments."""
		result = do_print(test_tree, PrintMode.full)

		for metric in test_metrics:
			assert f"# TYPE {metric.name} {metric.type}" in result

	def test_full_output_contains_metric_names(self, test_tree, test_metrics):
		"""Test that full mode contains metric names."""
		result = do_print(test_tree, PrintMode.full)

		for metric in test_metrics:
			# Each metric name should appear at least 3 times (HELP, TYPE, and standalone)
			assert result.count(metric.name) >= 3

	def test_full_output_format(self, test_tree):
		"""Test that full mode follows expected format."""
		result = do_print(test_tree, PrintMode.full)
		lines = result.split("\n")

		# Should have 3 lines per metric (HELP, TYPE, name)
		assert len(lines) == len(test_tree.metrics) * 3

	def test_full_empty_tree(self):
		"""Test full mode with empty tree."""
		empty_tree = MetricsTree({})
		result = do_print(empty_tree, PrintMode.full)
		assert result == ""

	def test_full_metric_without_help(self):
		"""Test full mode with metric without help text."""
		metric = Metric(name="test_metric", help="", type="counter", labels=[])
		tree = MetricsTree.mk_tree([metric])
		result = do_print(tree, PrintMode.full)

		assert "# HELP test_metric " in result
		assert "# TYPE test_metric counter" in result
		assert "test_metric" in result


class TestPrintModeTree:
	"""Tests for PrintMode.tree"""

	def test_tree_output_contains_all_metrics(self, test_tree, test_metrics):
		"""Test that tree mode contains all metric names."""
		result = do_print(test_tree, PrintMode.tree)

		for metric in test_metrics:
			assert metric.name in result or metric.name.split("_")[-1] in result

	def test_tree_output_uses_tabs(self, test_tree):
		"""Test that tree mode uses tabs for indentation."""
		result = do_print(test_tree, PrintMode.tree)

		# Should contain tabs if there's any hierarchy
		if len(test_tree.metrics) > 0:
			assert "\t" in result

	def test_tree_output_hierarchical_structure(self, test_tree):
		"""Test that tree mode creates hierarchical structure."""
		result = do_print(test_tree, PrintMode.tree)
		lines = result.split("\n")

		# Should have lines with different indentation levels
		indent_levels = set()
		for line in lines:
			if line:
				indent = len(line) - len(line.lstrip("\t"))
				indent_levels.add(indent)

		# With metrics that have underscores, we should have multiple indent levels
		assert len(indent_levels) > 1

	def test_tree_output_contains_types(self, test_tree, test_metrics):
		"""Test that tree mode contains metric types."""
		result = do_print(test_tree, PrintMode.tree)

		for metric in test_metrics:
			assert metric.type in result

	def test_tree_empty_tree(self):
		"""Test tree mode with empty tree."""
		empty_tree = MetricsTree({})
		result = do_print(empty_tree, PrintMode.tree)
		assert result == ""

	def test_tree_metric_without_underscore(self):
		"""Test tree mode with metric without underscore."""
		metric = Metric(name="simplemetric", help="A simple metric", type="gauge", labels=[])
		tree = MetricsTree.mk_tree([metric])
		result = do_print(tree, PrintMode.tree)

		assert "simplemetric" in result
		assert "(gauge)" in result


class TestPrintModeJson:
	"""Tests for PrintMode.json"""

	def test_json_output_is_valid_json(self, test_tree):
		"""Test that json mode produces valid JSON."""
		result = do_print(test_tree, PrintMode.json)

		# Should be parseable as JSON
		parsed = json.loads(result)
		assert isinstance(parsed, dict)

	def test_json_output_contains_all_metrics(self, test_tree, test_metrics):
		"""Test that json mode contains all metrics."""
		result = do_print(test_tree, PrintMode.json)
		parsed = json.loads(result)

		for metric in test_metrics:
			assert metric.name in parsed

	def test_json_output_contains_metric_attributes(self, test_tree, test_metrics):
		"""Test that json mode contains all metric attributes."""
		result = do_print(test_tree, PrintMode.json)
		parsed = json.loads(result)

		for metric in test_metrics:
			metric_data = parsed[metric.name]
			assert metric_data["name"] == metric.name
			assert metric_data["help"] == metric.help
			assert metric_data["type"] == metric.type

	def test_json_output_is_indented(self, test_tree):
		"""Test that json mode uses indentation."""
		result = do_print(test_tree, PrintMode.json)

		# Indented JSON should contain newlines
		assert "\n" in result
		# Should contain 2-space indentation
		assert "  " in result

	def test_json_empty_tree(self):
		"""Test json mode with empty tree."""
		empty_tree = MetricsTree({})
		result = do_print(empty_tree, PrintMode.json)
		parsed = json.loads(result)
		assert parsed == {}

	def test_json_metric_structure(self):
		"""Test json mode metric structure."""
		metric = Metric(name="test_metric", help="Test help", type="counter", labels=[])
		tree = MetricsTree.mk_tree([metric])
		result = do_print(tree, PrintMode.json)
		parsed = json.loads(result)

		assert "test_metric" in parsed
		assert parsed["test_metric"]["name"] == "test_metric"
		assert parsed["test_metric"]["help"] == "Test help"
		assert parsed["test_metric"]["type"] == "counter"
