import unittest
from typing import NewType
from unittest.mock import Mock

import pytest
from rich.text import Text
from textual.widgets.tree import TreeNode

from alpacloud.crdvis.models import OpenAPIV3Schema
from alpacloud.crdvis.vis import SearchMode, find_all_nodes, match_any, match_label

# Mock NodeID for testing
NodeID = NewType("NodeID", int)


# Mock Tree class for testing
class MockTree:
	def __init__(self):
		self._current_id = 0

	def process_label(self, label):
		if isinstance(label, str):
			return Text(label)
		return label

	def _new_id(self):
		id = self._current_id
		self._current_id += 1
		return NodeID(id)


class TestFindAllNodes(unittest.TestCase):
	"""Test cases for the find_all_nodes function."""

	def setUp(self):
		"""Set up test fixtures."""
		# Create a mock tree for testing
		self.mock_tree = MockTree()

		# Create a mock tree structure for testing
		self.root = TreeNode(self.mock_tree, None, NodeID(0), Text("Root"))
		self.child1 = TreeNode(self.mock_tree, self.root, NodeID(1), Text("Child 1"))
		self.child2 = TreeNode(self.mock_tree, self.root, NodeID(2), Text("Child 2"))
		self.grandchild1 = TreeNode(self.mock_tree, self.child1, NodeID(3), Text("Grandchild 1"))
		self.grandchild2 = TreeNode(self.mock_tree, self.child2, NodeID(4), Text("Grandchild 2"))

		# Set up the tree structure
		self.root._children = [self.child1, self.child2]
		self.child1._children = [self.grandchild1]
		self.child2._children = [self.grandchild2]

		# Add data to nodes for testing match_any
		schema1 = OpenAPIV3Schema(type="string", description="A string field")
		schema2 = OpenAPIV3Schema(type="integer", description="An integer field")

		self.root.data = schema1
		self.child1.data = schema2

	def test_find_all_nodes_with_find_mode(self):
		"""Test find_all_nodes with SearchMode.find."""
		# Should match nodes with "child" in label
		results = find_all_nodes("child", self.root, SearchMode.find)
		self.assertEqual(len(results), 4)  # Should find all child nodes

		# Should match nodes with "string" in description
		results = find_all_nodes("string", self.root, SearchMode.find)
		self.assertEqual(len(results), 1)  # Should find only the root node
		self.assertEqual(results[0], self.root)

		# Should match nodes with "integer" in description
		results = find_all_nodes("integer", self.root, SearchMode.find)
		self.assertEqual(len(results), 1)  # Should find only child1
		self.assertEqual(results[0], self.child1)

	def test_find_all_nodes_with_goto_mode(self):
		"""Test find_all_nodes with SearchMode.goto."""
		# Should match nodes with "child" in label
		results = find_all_nodes("child", self.root, SearchMode.goto)
		self.assertEqual(len(results), 4)  # Should find all child nodes

		# Should NOT match nodes with "string" in description (only checks labels)
		results = find_all_nodes("string", self.root, SearchMode.goto)
		self.assertEqual(len(results), 0)  # Should not find any nodes

	def test_find_all_nodes_case_insensitive(self):
		"""Test that find_all_nodes is case insensitive."""
		# Should match "ROOT" even though the label is "Root"
		results = find_all_nodes("ROOT", self.root, SearchMode.find)
		self.assertEqual(len(results), 1)
		self.assertEqual(results[0], self.root)

	def test_find_all_nodes_empty_search(self):
		"""Test find_all_nodes with an empty search string."""
		# Empty string should match all nodes
		results = find_all_nodes("", self.root, SearchMode.find)
		self.assertEqual(len(results), 5)  # Should find all nodes

	def test_find_all_nodes_no_matches(self):
		"""Test find_all_nodes with a search string that doesn't match any nodes."""
		results = find_all_nodes("nonexistent", self.root, SearchMode.find)
		self.assertEqual(len(results), 0)  # Should not find any nodes

	def test_find_all_nodes_invalid_search_mode(self):
		"""Test find_all_nodes with an invalid search mode."""
		with pytest.raises(TypeError):
			find_all_nodes("test", self.root, "invalid_mode")


class TestMatchFunctions(unittest.TestCase):
	"""Test cases for the match_label and match_any functions."""

	def setUp(self):
		"""Set up test fixtures."""
		# Create a mock tree for testing
		self.mock_tree = MockTree()

		# Create mock nodes for testing
		self.node_with_str_label = TreeNode(self.mock_tree, None, NodeID(0), Text("Test Label"))

		# Create a mock Text object for rich text label
		mock_text = Mock()
		mock_text.plain = "Rich Text Label"
		self.node_with_rich_label = TreeNode(self.mock_tree, None, NodeID(1), mock_text)

		# Add data to nodes for testing match_any
		schema = OpenAPIV3Schema(type="string", description="A test description")
		self.node_with_description = TreeNode(self.mock_tree, None, NodeID(2), Text("Node with Description"))
		self.node_with_description.data = schema

	def test_match_label_with_string_label(self):
		"""Test match_label with a string label."""
		self.assertTrue(match_label(self.node_with_str_label, "test"))
		self.assertFalse(match_label(self.node_with_str_label, "nonexistent"))

	def test_match_label_with_rich_label(self):
		"""Test match_label with a rich text label."""
		self.assertTrue(match_label(self.node_with_rich_label, "rich"))
		self.assertFalse(match_label(self.node_with_rich_label, "nonexistent"))

	def test_match_any_with_matching_label(self):
		"""Test match_any with a matching label."""
		self.assertTrue(match_any(self.node_with_str_label, "test"))

	def test_match_any_with_matching_description(self):
		"""Test match_any with a matching description."""
		self.assertTrue(match_any(self.node_with_description, "description"))

	def test_match_any_with_no_match(self):
		"""Test match_any with no match in label or description."""
		self.assertFalse(match_any(self.node_with_str_label, "nonexistent"))


if __name__ == "__main__":
	unittest.main()
