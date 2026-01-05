"""Tests for utility functions."""

import pytest

from alpacloud.promls.util import paths_to_tree


class TestPathsToTree:
	"""Tests for paths_to_tree function."""

	def test_simple_tree(self):
		"""Test basic tree construction."""
		mapping = {
			"a/b/c": 1,
			"a/b/d": 2,
			"a/x": 3,
			"z": 4,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"a": {
				"b": {"c": 1, "d": 2},
				"x": 3,
			},
			"z": 4,
		}

	def test_single_level(self):
		"""Test single-level paths (no nesting)."""
		mapping = {"a": 1, "b": 2, "c": 3}
		tree = paths_to_tree(mapping)
		assert tree == {"a": 1, "b": 2, "c": 3}

	def test_deep_nesting(self):
		"""Test deeply nested paths."""
		mapping = {"a/b/c/d/e/f": 42}
		tree = paths_to_tree(mapping)
		assert tree == {"a": {"b": {"c": {"d": {"e": {"f": 42}}}}}}

	def test_empty_mapping(self):
		"""Test with empty input."""
		mapping = {}
		tree = paths_to_tree(mapping)
		assert tree == {}  # pylint: disable=use-implicit-booleaness-not-comparison

	def test_custom_separator(self):
		"""Test with custom separator."""
		mapping = {
			"a_b_c": 1,
			"a_b_d": 2,
			"x": 3,
		}
		tree = paths_to_tree(mapping, sep="_")
		assert tree == {
			"a": {
				"b": {"c": 1, "d": 2},
			},
			"x": 3,
		}

	def test_empty_segments_ignored(self):
		"""Test that empty path segments are ignored."""
		mapping = {
			"a//b///c": 1,
			"a/b": 2,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"a": {
				"b": {"c": 1, "__value__": 2},
			},
		}

	def test_branch_and_leaf_conflict_with_leaf_key(self):
		"""Test node that is both branch and leaf with leaf_key."""
		mapping = {
			"a/b": 1,
			"a/b/c": 2,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"a": {
				"b": {
					"__value__": 1,
					"c": 2,
				},
			},
		}

	def test_branch_and_leaf_conflict_without_leaf_key(self):
		"""Test that conflict raises ValueError when leaf_key is None."""
		mapping = {
			"a/b": 1,
			"a/b/c": 2,
		}
		with pytest.raises(ValueError, match="leaf_key=None"):
			paths_to_tree(mapping, leaf_key=None)

	def test_leaf_promoted_to_branch_with_leaf_key(self):
		"""Test promoting a leaf to branch when a child is added."""
		mapping = {
			"a/b/c": 1,
			"a/b": 2,  # This comes after a/b/c, so b is already a dict
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"a": {
				"b": {
					"c": 1,
					"__value__": 2,
				},
			},
		}

	def test_leaf_promoted_to_branch_without_leaf_key(self):
		"""Test that promoting leaf to branch raises ValueError when leaf_key is None."""
		# Need to insert in order where leaf comes first
		mapping = {
			"a": 1,
			"a/b": 2,
		}
		with pytest.raises(ValueError, match="cannot turn leaf into branch"):
			paths_to_tree(mapping, leaf_key=None)

	def test_custom_leaf_key(self):
		"""Test with custom leaf_key."""
		mapping = {
			"a/b": 1,
			"a/b/c": 2,
		}
		tree = paths_to_tree(mapping, leaf_key="@value")
		assert tree == {
			"a": {
				"b": {
					"@value": 1,
					"c": 2,
				},
			},
		}

	def test_root_value_with_leaf_key(self):
		"""Test storing value at root path (empty string)."""
		mapping = {
			"": 1,
			"a": 2,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"__value__": 1,
			"a": 2,
		}

	def test_root_value_without_leaf_key(self):
		"""Test that root value raises ValueError when leaf_key is None."""
		mapping = {
			"": 1,
		}
		with pytest.raises(ValueError, match="Cannot store root value"):
			paths_to_tree(mapping, leaf_key=None)

	def test_separator_only_path(self):
		"""Test path with only separators (treated as root)."""
		mapping = {
			"///": 1,
			"a": 2,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"__value__": 1,
			"a": 2,
		}

	def test_mixed_types_as_values(self):
		"""Test with various value types."""
		mapping = {
			"int": 42,
			"str": "hello",
			"list": [1, 2, 3],
			"dict": {"nested": "value"},
			"none": None,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"int": 42,
			"str": "hello",
			"list": [1, 2, 3],
			"dict": {"nested": "value"},
			"none": None,
		}

	def test_complex_tree_structure(self):
		"""Test a more complex tree structure."""
		mapping = {
			"http/server/requests/total": 100,
			"http/server/requests/errors": 5,
			"http/server/latency": 50,
			"http/client/requests/total": 80,
			"http/client/requests/errors": 2,
			"database/queries/total": 200,
			"database/queries/slow": 10,
		}
		tree = paths_to_tree(mapping)
		assert tree == {
			"http": {
				"server": {
					"requests": {
						"total": 100,
						"errors": 5,
					},
					"latency": 50,
				},
				"client": {
					"requests": {
						"total": 80,
						"errors": 2,
					},
				},
			},
			"database": {
				"queries": {
					"total": 200,
					"slow": 10,
				},
			},
		}

	def test_underscore_separator_like_prometheus(self):
		"""Test with underscore separator (like Prometheus metrics)."""
		mapping = {
			"http_server_requests_total": 100,
			"http_server_requests_errors": 5,
			"http_client_requests_total": 80,
		}
		tree = paths_to_tree(mapping, sep="_")
		assert tree == {
			"http": {
				"server": {
					"requests": {
						"total": 100,
						"errors": 5,
					},
				},
				"client": {
					"requests": {
						"total": 80,
					},
				},
			},
		}

	def test_branch_to_leaf_promotion_order_matters(self):
		"""Test that insertion order matters for promotion."""
		# When leaf is inserted before branches
		mapping1 = {
			"a": 1,
			"a/b": 2,
			"a/c": 3,
		}
		tree1 = paths_to_tree(mapping1)
		assert tree1 == {
			"a": {
				"__value__": 1,
				"b": 2,
				"c": 3,
			},
		}

		# When branches are inserted before leaf
		mapping2 = {
			"a/b": 2,
			"a/c": 3,
			"a": 1,
		}
		tree2 = paths_to_tree(mapping2)
		assert tree2 == {
			"a": {
				"b": 2,
				"c": 3,
				"__value__": 1,
			},
		}
