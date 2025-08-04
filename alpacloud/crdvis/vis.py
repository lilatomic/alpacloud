"""
CRDVis visualization module for displaying Kubernetes CRD resources.
"""

import os

import yaml
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Tree
from textual.widgets.tree import TreeNode

from alpacloud.crdvis.models import CustomResourceDefinition


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
		sample_crd_path = os.path.join(current_dir, "alpacloud", "crdvis", "test_resources", "sample_crd.yaml")

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

			# Add basic information
			self._add_node(root, "Name", first_version.name)
			self._add_node(root, "Served", str(first_version.served))
			self._add_node(root, "Storage", str(first_version.storage))

			# Add schema information
			if first_version.schema:
				schema_node = root.add("Schema")
				for schema_key, schema_value in first_version.schema.items():
					schema_item = schema_node.add(schema_key)
					if hasattr(schema_value, "type"):
						self._add_node(schema_item, "Type", schema_value.type)
					if hasattr(schema_value, "properties"):
						props_node = schema_item.add("Properties")
						for prop_name, prop_value in schema_value.properties.items():
							prop_node = props_node.add(prop_name)
							self._add_node(prop_node, "Type", prop_value.type)

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


def main():
	"""Run the CRD Visualizer app."""
	app = CRDVisApp()
	app.run()


if __name__ == "__main__":
	main()
