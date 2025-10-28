"""Generic utilities."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, TypeAlias, TypeVar

T = TypeVar("T")
TreeT: TypeAlias = Dict[str, "TreeT" | T]


def paths_to_tree(
	mapping: Mapping[str, T],
	*,
	sep: str = "/",
	leaf_key: Optional[str] = "__value__",
) -> TreeT[T]:
	"""
	Convert a mapping of path strings to a tree of nested dicts.

	Example:
		mapping = {
			"a/b/c": 1,
			"a/b/d": 2,
			"a/x": 3,
			"z": 4,
		}
		tree = paths_to_tree(mapping)
		# tree:
		# {
		#   "a": {
		#     "b": {"c": 1, "d": 2},
		#     "x": 3
		#   },
		#   "z": 4
		# }

	Behavior:
	  - Empty path segments are ignored (e.g., "a//b" behaves like "a/b").
	  - If a node needs to be both a branch and a leaf, the leaf value is
		stored under `leaf_key` inside that node (if `leaf_key` is not None).
	  - If `leaf_key` is None, such conflicts raise ValueError.

	Args:
	  mapping: dict of "path" -> value
	  sep: path separator (default "/")
	  leaf_key: key for storing a node's own value when it also has children.
				If None, conflicts raise ValueError.

	Returns:
	  A nested dict tree.
	"""
	root: Dict[str, Any] = {}

	for path, value in mapping.items():
		parts = [p for p in path.split(sep) if p]  # skip empty segments

		# Special case: value at root path (e.g., "" or only separators)
		if not parts:
			if leaf_key is None:
				raise ValueError("Cannot store root value when leaf_key=None")
			existing = root.get(leaf_key)
			# Overwrite by default; change here if you prefer strict handling
			root[leaf_key] = value
			continue

		node = root
		for i, part in enumerate(parts):
			is_last = i == len(parts) - 1
			existing = node.get(part)

			if is_last:
				if existing is None:
					node[part] = value
				elif isinstance(existing, dict):
					if leaf_key is None:
						raise ValueError(f"Conflict at '{sep.join(parts[: i + 1])}': node already a branch and leaf_key=None")
					# Store value alongside existing children
					existing[leaf_key] = value
				else:
					# Overwrite existing leaf at the same path
					node[part] = value
			else:
				if existing is None:
					child: Dict[str, Any] = {}
					node[part] = child
					node = child
				elif isinstance(existing, dict):
					node = existing
				else:
					# Need to descend but found a leaf: promote to branch
					if leaf_key is None:
						raise ValueError(f"Conflict at '{sep.join(parts[: i + 1])}': cannot turn leaf into branch when leaf_key=None")
					promoted: Dict[str, Any] = {leaf_key: existing}
					node[part] = promoted
					node = promoted

	return root
