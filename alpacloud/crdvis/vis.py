"""
CRDVis visualization module for displaying Kubernetes CRD resources.
"""

import os

import yaml
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

from alpacloud.crdvis.models import CustomResourceDefinition, OpenAPIV3, OpenAPIV3Array, OpenAPIV3Enum, OpenAPIV3Schema, OpenAPIV3Union, OpenAPIV3Dict


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

	def is_simple(self, openapi_node: OpenAPIV3) -> bool:
		if isinstance(openapi_node, OpenAPIV3Schema):
			return openapi_node.type in ("string", "integer", "number", "boolean")
		elif isinstance(openapi_node, OpenAPIV3Union):
			return 				 all(self.is_simple(e) for e in openapi_node.anyOf)
		elif isinstance(openapi_node, OpenAPIV3Enum):
			return False
		elif isinstance(openapi_node, OpenAPIV3Array):
			return self.is_simple(openapi_node.items)
		elif isinstance(openapi_node, OpenAPIV3Dict):
			return self.is_simple(openapi_node.additionalProperties)
		else:
			return True

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

		return schema_item


def main():
	"""Run the CRD Visualizer app."""
	app = CRDVisApp()
	app.run()


if __name__ == "__main__":
	main()
