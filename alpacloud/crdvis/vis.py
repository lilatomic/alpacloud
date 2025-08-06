"""
CRDVis visualization module for displaying Kubernetes CRD resources.
"""

import enum
import os
import shutil
import subprocess
from textwrap import dedent
from typing import Any, Callable
from urllib.parse import urlparse

import requests
import yaml
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import Reactive, reactive
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Label, Static, TextArea, Tree
from textual.widgets.tree import TreeNode

from alpacloud.crdvis.models import CustomResourceDefinition, OpenAPIV3, OpenAPIV3Array, OpenAPIV3Dict, OpenAPIV3Enum, OpenAPIV3Schema, OpenAPIV3Union


class InfoBox(Widget):
	"""A widget to display information about the selected CRD."""

	crd: Reactive[CustomResourceDefinition | None] = reactive(None)

	def __init__(self) -> None:
		super().__init__()

	DEFAULT_CSS = """\
	InfoBox {
		width: 100%;
		height: auto;
		margin: 0 0 0 0;
	}
	InfoBox > Horizontal {
		width: 100%;
		height: auto;
	}
	InfoBox > Horizontal > Container {
		height: auto;
	}
	.left {
		align: left middle;
	}
	.right {
		align: right middle;
	}
	"""

	def watch_crd(self, crd: CustomResourceDefinition) -> None:
		"""Update the info box when the CRD changes."""
		self.remove_children()
		if not crd:
			self.mount(Label("No CRD selected"))
		else:
			self.mount(
				Horizontal(
					Container(Label(crd.spec.names.kind), classes="left"),
					Container(Label(crd.spec.group), classes="right"),
				)
			)


class FindBox(Input):
	"""A widget to search for a node in the tree."""

	BINDINGS = [
		("enter", "search", "Search"),
		Binding("ctrl+c", "clear", "clear", show=False),
	]

	def __init__(self, placeholder: str, find_method: Callable, id: str = "find-box") -> None:
		self.find_method = find_method
		super().__init__(placeholder, id=id)

	async def action_search(self):
		await self.find_method(self.value)

	def action_clear(self) -> None:
		"""Clear the text area."""
		self.clear()


class SearchMode(enum.Enum):
	"""How to search for fields in the CRD"""

	find = "find"
	goto = "goto"


class OpenDialog(ModalScreen):
	"""Modal to open a CRD from a variety of sources."""

	BINDINGS = [
		Binding("escape", "cancel", "Cancel", priority=True),
		Binding("enter", "submit", "Submit", priority=True),
	]

	DEFAULT_CSS = """
	OpenDialog {
		align: center middle;
	}

	OpenDialog > Container {
		width: auto;
		height: auto;
		border: thick $background 80%;
		background: $surface;
		margin: 1;
	}

	OpenDialog > Container > Label {
		width: 100%;
		content-align-horizontal: center;
		margin: 1;
	}

	OpenDialog > Container > TextArea {
		width: 100%;
		height: auto;
		max-height: 40%;
		content-align-horizontal: center;
		margin: 1;
	}

	OpenDialog > Container > Horizontal {
		width: auto;
		height: auto;
		margin: 1 1;
	}

	OpenDialog > Container > Horizontal > Button {
		margin: 1 1;
	}
	"""

	def compose(self) -> ComposeResult:
		"""Create child widgets for the modal."""
		with Container():
			yield Label("Open a CRD file")
			yield Static(
				dedent("""\
				supported sources:
				- `file://` : a file (will also work for base paths that exist on disk)
				- `http://` | `https://` : a URL to a CRD on the internet. (for GitHub, will automatically navigate to the raw file)
				- `kubectl://` : a CRD in your cluster
				- raw : just copypaste the CRD
			""")
			)
			yield TextArea()
			with Horizontal():
				yield Button("Open", variant="primary", id="open-dialog-open")
				yield Button("Cancel", variant="warning", id="open-dialog-cancel")

	def _submit(self):
		"""Return the target"""
		input_widget = self.query_one(TextArea)
		self.dismiss(input_widget.text)

	def _cancel(self):
		"""Cancel the dialog"""
		self.dismiss(None)

	def action_submit(self) -> None:
		self._submit()

	def action_cancel(self) -> None:
		self._cancel()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "open-dialog-open":
			self._submit()
		elif event.button.id == "open-dialog-cancel":
			self._cancel()


class CRDVisApp(App):
	"""A Textual app to visualize Kubernetes CRDs."""

	TITLE = "CRD Visualizer"
	CSS = """
	Screen {
		overflow-y: auto;
	}
	.derscription-box {
        height: 25%;
        overflow-y: auto;
	}
    .description-area {
        background: $surface;
        color: $text;
        border-top: tall $primary;
        padding: 1 2;
    }
	.find-box {
		border-top: none;
		padding: 0 0;
	}
    """

	CSS_PATH = None  # We're not using custom CSS for this skeleton

	BINDINGS = [
		Binding("ctrl+g", "goto", "goto", priority=True),
		Binding("ctrl+f", "find", "find", priority=True),
		Binding("ctrl+o", "open_dialog", "Open file", priority=True),
	]

	search_mode = SearchMode.find
	crd: CustomResourceDefinition | None = None

	def compose(self) -> ComposeResult:
		"""Create child widgets for the app."""
		yield Header()
		yield InfoBox()
		yield Tree("CRD Version")
		yield Vertical(Static(classes="description-area"), classes="derscription-box")
		yield FindBox(placeholder="Find...", id="find-box", find_method=self.do_find)
		yield Footer()

	def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
		"""Handle node selection in the tree."""
		from textual.widgets import Static

		text_area = self.query_one(Static)
		node = event.node
		# Check if this is an OpenAPI node that might have a description
		text = Text("")

		if hasattr(node, "data"):
			data = node.data
			if description := getattr(data, "description", None):
				text += description
			if pattern := getattr(data, "pattern", None):
				text += Text(f"\nPattern: {pattern}", style="bold")

			# add enum values
			if isinstance(data, OpenAPIV3Enum):
				text += Text("\nValues:", style="bold")
				for enum_value in data.enum:
					text += Text(f"\n- {enum_value}")

		text_area.update(text)

	def on_mount(self) -> None:
		"""Load the CRD and populate the tree when the app starts."""
		# Get the path to the sample CRD file
		current_dir = os.getcwd()
		sample_crd_path = os.path.join(current_dir, "alpacloud", "crdvis", "test_resources", "podmonitor.yaml")

		crd = self.read_path("file://" + sample_crd_path)
		if crd:
			self.load_crd(crd)

	def read_path(self, path: str) -> CustomResourceDefinition | None:
		"""
		Read a path-like object to fetch a CRD.
		"""
		if path.startswith("http://") or path.startswith("https://"):
			req = requests.Request("GET", path)

			url = urlparse(req.url)
			if url.netloc == "github.com":
				req.params["raw"] = "true"

			response = requests.Session().send(req.prepare(), timeout=30)

			if not response.ok:
				self.notify(f"Failed to fetch CRD from {path}: {response.status_code}", severity="error")
				return None
			content = response.text
		elif path.startswith("file://") or os.path.exists(path):
			disk_path = path.rsplit("://", 1)[-1]
			if not os.path.exists(disk_path):
				self.notify(f"File not found: {disk_path}", severity="error")
				return None

			with open(disk_path, "r", encoding="utf-8") as f:
				content = f.read()

		elif path.startswith("kubectl://"):
			kubectl_crd = path.rsplit("://", 1)[-1]
			kubectl_exe = shutil.which("kubectl")
			if not kubectl_exe:
				self.notify("kubectl is not installed.", severity="error")
				return None

			try:
				content = subprocess.check_output([kubectl_exe, "get", "-o", "yaml", "crd", kubectl_crd], timeout=30).decode("utf-8")
			except subprocess.SubprocessError as e:
				try:
					crds = subprocess.check_output([kubectl_exe, "get", "crd"], timeout=30)
					if crds:
						self.notify(f"crd is not available in cluster {kubectl_crd}", severity="error")
					else:
						self.notify(f"Failed to fetch CRDs {kubectl_crd}: {e}", severity="error")

				except subprocess.SubprocessError as e:
					self.notify(f"Failed to fetch CRDs {kubectl_crd}: {e}", severity="error")
				return None
		else:
			content = path

		if not content:
			return None
		doc = yaml.safe_load(content)
		return CustomResourceDefinition.model_validate(doc)

	def load_crd(self, crd: CustomResourceDefinition) -> None:
		"""Load the CRD into the app."""
		self.crd = crd
		self.query_one(InfoBox).crd = crd

		# Get the first CRD version
		if crd.spec.versions:
			first_version = crd.spec.versions[0]

			# Get the tree widget and populate it
			tree = self.query_one(Tree)
			tree.clear()
			root = tree.root
			root.label = f"CRD Version: {first_version.name}"

			# Add basic information (non-expandable)
			root.add_leaf(f"Name: {first_version.name}")
			value = str(first_version.served)
			root.add_leaf(f"Served: {value}")
			value1 = str(first_version.storage)
			root.add_leaf(f"Storage: {value1}")

			# Add schema information
			if first_version.openAPIV3Schema:
				openapi = first_version.openAPIV3Schema.openAPIV3Schema
				self.add_openapi_node(root, "Schema", openapi)

			# Add selectable fields
			if first_version.selectableFields:
				fields_node = root.add("Selectable Fields")
				for field in first_version.selectableFields:
					fields_node.add(f"JsonPath: {field.jsonPath}")

			# Add printer columns
			if first_version.additionalPrinterColumns:
				columns_node = root.add("Additional Printer Columns")
				for column in first_version.additionalPrinterColumns:
					column_node = columns_node.add(column.name)
					column_node.add(f"JsonPath: {column.jsonPath}")
					column_node.add(f"Type: {column.type}")

			# Expand the tree
			root.expand()

	def is_simple(self, openapi_node: OpenAPIV3) -> bool:
		"""Whether the given OpenAPI node is a simple (primitive) type whose representation we should inline"""
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
		"""Identify what we should use for the type"""
		match openapi_node:
			case OpenAPIV3Schema():
				if openapi_node.format:
					return openapi_node.format
				else:
					return openapi_node.type
			case OpenAPIV3Union():
				if self.is_simple(openapi_node):
					return f"Union{[self.find_typename(e) for e in openapi_node.anyOf]}"
				else:
					return "Union"
			case OpenAPIV3Enum():
				return "Enum"
			case OpenAPIV3Array():
				if self.is_simple(openapi_node.items):
					return rf"Array\[{self.find_typename(openapi_node.items)}]"
				else:
					return r"Array\[object]"
			case OpenAPIV3Dict():
				if self.is_simple(openapi_node):
					return rf"Dict\[string, {self.find_typename(openapi_node.additionalProperties)}]"
				else:
					return "Dict"
			case _:
				raise TypeError(f"Unexpected type: {type(openapi_node)}")

	def add_openapi_node(self, parent_node, name, openapi_node):
		"""Add an OpenAPI node to the tree"""
		k = f"{name}: {self.find_typename(openapi_node)}"
		match openapi_node:
			case OpenAPIV3Schema():
				if openapi_node.type == "object":
					schema_item = parent_node.add(k)
				else:
					schema_item = parent_node.add_leaf(k)

				if openapi_node.properties:
					for prop_name, prop in openapi_node.properties.items():
						self.add_openapi_node(schema_item, prop_name, prop)

			case OpenAPIV3Union():
				if self.is_simple(openapi_node):
					schema_item = parent_node.add_leaf(k)
				else:
					schema_item = parent_node.add(k)
					for e in openapi_node.anyOf:
						self.add_openapi_node(schema_item, "Option", e)

			case OpenAPIV3Array():
				if self.is_simple(openapi_node.items):
					schema_item = parent_node.add_leaf(k)

				else:
					schema_item = parent_node.add(k)
					items_node = self.add_openapi_node(schema_item, "Items", openapi_node.items)
					items_node.expand()

			case OpenAPIV3Enum():
				schema_item = parent_node.add(k)

			case OpenAPIV3Dict():
				if self.is_simple(openapi_node):
					schema_item = parent_node.add_leaf(k)

				else:
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
		self.search_mode = SearchMode.goto
		findbox.focus()

	async def action_find(self) -> None:
		findbox = self.query_one(FindBox)
		self.search_mode = SearchMode.find
		findbox.focus()

	async def action_open_dialog(self) -> None:
		"""Open the file open dialog."""
		dialog = OpenDialog()

		def o(path: Any) -> None:
			if path and isinstance(path, str):
				crd = self.read_path(path)
				if crd:
					self.load_crd(crd)

		await self.push_screen(dialog, o)

	async def do_find(self, s: str):
		"""
		Implementation of the search functionality.

		The search proceeds in steps:
		- find all matches
		- find where our current cursor is
		- focus to the next match

		This allows mashing the find button to get the next result.
		It _could_ allow for finding from the current position, but it does not.
		"""
		all_results = self.find_all_nodes(s, self.query_one(Tree).root)

		if not all_results:
			self.notify("No node found with the given label.")
			return

		cursor = self.query_one(Tree).cursor_node
		try:
			if cursor:
				current = all_results.index(cursor)
			else:
				current = -1
		except ValueError:
			current = -1
		found = all_results[(current + 1) % len(all_results)]
		await self._focus_to_node(found)

	def find_all_nodes(self, s: str, cursor: TreeNode) -> list[TreeNode]:
		"""Find a node in the tree by its label."""
		found = []

		match self.search_mode:
			case SearchMode.find:
				search_predicate = match_any
			case SearchMode.goto:
				search_predicate = match_label
			case _:
				raise TypeError(f"Invalid search mode: {self.search_mode}")

		if search_predicate(cursor, s):
			found.append(cursor)

		for child in cursor.children:
			nodes = self.find_all_nodes(s, child)
			if nodes:
				found.extend(nodes)

		return found


def match_label(node: TreeNode[OpenAPIV3], s: str) -> bool:
	"""Check if a label matches a substring."""
	if isinstance(node.label, str):
		tgt = node.label.lower()
	else:
		tgt = node.label.plain.lower()
	return s.lower() in tgt


def match_any(node: TreeNode[OpenAPIV3], s: str) -> bool:
	"""Check if a given OpenAPI node matches a substring."""
	if match_label(node, s):
		return True
	else:
		data = node.data
		if description := getattr(data, "description", None):
			return s.lower() in description.lower()
	return False


def main():
	"""Run the CRD Visualizer app."""
	CRDVisApp().run()


if __name__ == "__main__":
	main()
