"""
CRDVis visualization module for displaying Kubernetes CRD resources.
"""

import os
from typing import Callable

import yaml
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree, TextArea, Input
from textual.widgets.tree import TreeNode

from alpacloud.crdvis.models import CustomResourceDefinition, OpenAPIV3, OpenAPIV3Array, OpenAPIV3Enum, OpenAPIV3Schema, OpenAPIV3Union, OpenAPIV3Dict



class FindBox(Input):
	BINDINGS = [("enter", "find", "Find")]

	def __init__(self, placeholder: str, id: str = "find-box", find_method: Callable = None) -> None:
		self.find_method = find_method
		super().__init__(placeholder, id=id)

	async def action_find(self):
		await self.find_method(self.value)


class CRDVisApp(App):
	"""A Textual app to visualize Kubernetes CRDs."""

	TITLE = "CRD Visualizer"
	CSS = """
    .description-area {
        height: 25%;
        background: $surface;
        color: $text;
        border-top: tall $primary;
        padding: 1 2;
    }
	.find-box {
		border: none;
		padding: 0 0;
		dock: bottom;
	}
    """

	CSS_PATH = None  # We're not using custom CSS for this skeleton

	BINDINGS = [
		("ctrl+g", "goto", "goto"),
	]

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""
		yield Header()
		yield Tree("CRD Version")
		yield TextArea(read_only=True, classes="description-area")
		yield FindBox(placeholder="Find...", id="find-box", find_method=self.do_find)
		yield Footer()

	def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
		"""Handle node selection in the tree."""
		text_area = self.query_one(TextArea)
		node = event.node
		# Check if this is an OpenAPI node that might have a description
		if hasattr(node, "data"):
			data = node.data
			if hasattr(data, "description"):
				description = node.data.description or ""
				text_area.load_text(description)
			else:
				text_area.load_text("")
		else:
			text_area.load_text("")


	def on_mount(self) -> None:
		"""Load the CRD and populate the tree when the app starts."""
		# Get the path to the sample CRD file
		current_dir = os.getcwd()
		sample_crd_path = os.path.join(current_dir, "alpacloud", "crdvis", "test_resources", "podmonitor.yaml")

		# Load and deserialize the CRD
		with open(sample_crd_path, "r") as f:
			crd_dict = yaml.safe_load(f)

		crd = CustomResourceDefinition.parse_obj(crd_dict)

		# Get the first CRD version
		if crd.spec.versions:
			first_version = crd.spec.versions[0]

			# Get the tree widget and populate it
			tree = self.query_one(Tree)
			root = tree.root
			root.label = f"CRD Version: {first_version.name}"

			# Add basic information (non-expandable)
			self._add_leaf_node(root, "Name", first_version.name)
			self._add_leaf_node(root, "Served", str(first_version.served))
			self._add_leaf_node(root, "Storage", str(first_version.storage))

			# Add schema information
			if first_version.openAPIV3Schema:
				# schema_node = root.add("Schema")
				openapi = first_version.openAPIV3Schema.openAPIV3Schema
				self.add_openapi_node(root, "Schema", openapi)

			# Add selectable fields
			if first_version.selectableFields:
				fields_node = root.add("Selectable Fields")
				for field in first_version.selectableFields:
					self._add_node(fields_node, "JsonPath", field.jsonPath)

			# Add printer columns
			if first_version.additionalPrinterColumns:
				columns_node = root.add("Additional Printer Columns")
				for column in first_version.additionalPrinterColumns:
					column_node = columns_node.add(column.name)
					self._add_node(column_node, "JsonPath", column.jsonPath)
					self._add_node(column_node, "Type", column.type)

			# Expand the tree
			root.expand()

	def _add_node(self, parent: TreeNode, key: str, value: str) -> TreeNode:
		"""Helper method to add a key-value node to the tree."""
		return parent.add(f"{key}: {value}")

	def _add_leaf_node(self, parent: TreeNode, key: str, value: str) -> None:
		"""Helper method to add a non-expandable key-value node to the tree."""
		# Simply add the node without returning it, so no children can be added
		parent.add_leaf(f"{key}: {value}")

	def is_simple(self, openapi_node: OpenAPIV3) -> bool:
		match openapi_node:
			case OpenAPIV3Schema():
				return openapi_node.type in ("string", "integer", "number", "boolean")
			case OpenAPIV3Union():
				return all(self.is_simple(e) for e in openapi_node.anyOf)
			case OpenAPIV3Enum():
				return False
			case OpenAPIV3Array():
				return self.is_simple(openapi_node.items)
			case OpenAPIV3Dict():
				return self.is_simple(openapi_node.additionalProperties)
			case _:
				raise TypeError(f"Unexpected type: {type(openapi_node)}")

	def find_typename(self, openapi_node: OpenAPIV3) -> str:
		match openapi_node:
			case OpenAPIV3Schema():
				if openapi_node.format:
					return openapi_node.format
				else:
					return openapi_node.type
			# case OpenAPIV3Union():
			# 	return "Union"
			case OpenAPIV3Enum():
				return "Enum"
			case OpenAPIV3Array():
				if self.is_simple(openapi_node.items):
					return f"Array\[{self.find_typename(openapi_node.items)}]"
				else:
					return "Array\[object]"
			case OpenAPIV3Dict():
				return "Dict"
			case _:
				raise TypeError(f"Unexpected type: {type(openapi_node)}")

	def add_openapi_node(self, parent_node, name, openapi_node):
		match openapi_node:
			case OpenAPIV3Schema():
				k = f"{name}: {self.find_typename(openapi_node)}"

				if openapi_node.type == "object":
					schema_item = parent_node.add(k)
				else:
					schema_item = parent_node.add_leaf(k)

				if openapi_node.properties:
					for prop_name, prop in openapi_node.properties.items():
						self.add_openapi_node(schema_item, prop_name, prop)

			case OpenAPIV3Union():
				if self.is_simple(openapi_node):
					k = f"{name}: Union{[self.find_typename(e) for e in openapi_node.anyOf]}"
					schema_item = parent_node.add_leaf(k)
				else:
					k = f"{name}: Union"
					schema_item = parent_node.add(k)
					for e in openapi_node.anyOf:
						self.add_openapi_node(schema_item, "Option", e)

			case OpenAPIV3Array():
				k = rf"{name}: {self.find_typename(openapi_node)}"
				if self.is_simple(openapi_node.items):
					schema_item = parent_node.add_leaf(k)

				else:
					schema_item = parent_node.add(k)
					items_node = self.add_openapi_node(schema_item, "Items", openapi_node.items)
					items_node.expand()

			case OpenAPIV3Enum():
				k = f"{name}: {self.find_typename(openapi_node)}"
				schema_item = parent_node.add(k)
				for enum_value in openapi_node.enum:
					self._add_leaf_node(schema_item, "Value", enum_value)

			case OpenAPIV3Dict():
				if self.is_simple(openapi_node):
					k = f"{name}: {self.find_typename(openapi_node)}\[string, {self.find_typename(openapi_node.additionalProperties)}]"
					schema_item = parent_node.add_leaf(k)

				else:
					k = f"{name}: {self.find_typename(openapi_node)}"
					schema_item = parent_node.add(k)
					self.add_openapi_node(schema_item, "Items", openapi_node.additionalProperties)


			case _:
				raise TypeError(f"Unexpected type: {type(openapi_node)}")


		schema_item.data = openapi_node
		return schema_item

	async def _focus_to_node(self, node: TreeNode) -> None:
		"""Focus the tree widget on the given node."""
		tree = self.query_one(Tree)

		parent = node.parent
		while parent:
			parent.expand()
			parent = parent.parent

		tree.select_node(node)


	async def action_goto(self) -> None:
		findbox = self.query_one(FindBox)
		findbox.focus()

	async def do_find(self, s: str):
		found = self.find_node_start(s)
		if found:
			await self._focus_to_node(found)
			self.notify(f"Found node with label '{found.label}'.")
		else:
			self.notify("No node found with the given label.")

	def find_node_start(self, s: str) -> TreeNode | None:
		return self.find_node(s, self.query_one(Tree).root)

	def find_node(self, s: str, cursor: TreeNode) -> TreeNode | None:
		"""Find a node in the tree by its label."""
		if s in cursor.label:
			return cursor
		else:
			for child in cursor.children:
				node = self.find_node(s, child)
				if node:
					return node
			return None

def main():
	"""Run the CRD Visualizer app."""
	app = CRDVisApp()
	app.run()


if __name__ == "__main__":
	main()
