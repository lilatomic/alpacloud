"""
CRDVis visualization module for displaying Kubernetes CRD resources.
"""

import os

import yaml
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

from alpacloud.crdvis.models import CustomResourceDefinition, OpenAPIV3Array, OpenAPIV3Schema, OpenAPIV3Union, OpenAPIV3Enum


class CRDVisApp(App):
	"""A Textual app to visualize Kubernetes CRDs."""

	TITLE = "CRD Visualizer"
	CSS_PATH = None  # We're not using custom CSS for this skeleton

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""
		yield Header()
		yield Tree("CRD Version")
		yield Footer()

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

	def add_openapi_node(self, parent_node, name, openapi_node):
		match openapi_node:
			case OpenAPIV3Schema():
				k = f"{name}: {openapi_node.type}"

				if openapi_node.type == "object":
					schema_item = parent_node.add(k)
				else:
					schema_item = parent_node.add_leaf(k)

				if openapi_node.properties:
					for prop_name, prop in openapi_node.properties.items():
						self.add_openapi_node(schema_item, prop_name, prop)

			case OpenAPIV3Union():
				all_simple_types = all(e.type != "object" for e in openapi_node.anyOf)

				if all_simple_types:
					k = f"{name}: Union{[e.type for e in openapi_node.anyOf]}"
					schema_item = parent_node.add_leaf(k)
				else:
					k = f"{name}: Union"
					schema_item = parent_node.add(k)
					for e in openapi_node.anyOf:
						self.add_openapi_node(schema_item, "Option", e)

			case OpenAPIV3Array():
				k = f"{name}: Array"
				schema_item = parent_node.add(k)
				items_node = self.add_openapi_node(schema_item, "Items", openapi_node.items)
				items_node.expand()

			case OpenAPIV3Enum():
				k = f"{name}: Enum"
				schema_item = parent_node.add(k)
				for enum_value in openapi_node.enum:
					self._add_leaf_node(schema_item, "Value", enum_value)

			case _:
				raise TypeError(f"Unexpected type: {type(openapi_node)}")

		return schema_item


def main():
	"""Run the CRD Visualizer app."""
	app = CRDVisApp()
	app.run()


if __name__ == "__main__":
	main()
