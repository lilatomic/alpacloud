"""Promls metrics visualizer."""

import re

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import Reactive, reactive
from textual.screen import Screen, ScreenResultType
from textual.widget import Widget
from textual.widgets import Collapsible, Footer, Header, Input, Label, Static, Tree

from alpacloud.promls.fetch import ParseError
from alpacloud.promls.filter import MetricsTree, PredicateFactory, filter_any, filter_name
from alpacloud.promls.metrics import Metric
from alpacloud.promls.util import TreeT, paths_to_tree


class FindBox(Input):
	"""A widget to search for a node in the tree."""

	BINDINGS = [
		Binding("ctrl+c", "clear", "clear", show=False),
	]

	def __init__(self, placeholder: str, id: str = "find-box") -> None:
		super().__init__(placeholder=placeholder, id=id)

	def action_clear(self):
		"""Clear the text area."""
		self.clear()


class ErrorsModal(Screen):
	"""A modal widget to display errors."""

	BINDINGS = [
		Binding("ctrl+e", "dismiss", "Close", show=False),
		Binding("escape", "dismiss", "Close", show=False),
	]

	def __init__(self, errors: list[ParseError], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.errors = errors

	def compose(self):
		"""Textual compose"""
		with Vertical():
			yield Label("Parse Errors")
			for i, err in enumerate(self.errors):
				yield Static(f"error {i}: {str(err)}", classes="error")

	async def action_dismiss(self, result: ScreenResultType | None = None):
		"""Dismiss the modal."""
		await self.dismiss()


class MetricInfoBox(Widget):
	"""A widget to display information about the selected Metric."""

	metric: Reactive[Metric | None] = reactive(None, recompose=True)
	expand_labels: bool = False

	def compose(self) -> ComposeResult:
		"""Textual compose"""
		with Vertical():
			if not self.metric:
				yield Label("Metric Info")
			else:
				with Horizontal():
					yield Container(Label(self.metric.name, variant="accent"), classes="left")
					yield Container(Label(self.metric.type, variant="accent"), classes="right")
				yield Static(self.metric.help)

				with Collapsible(title="Labels", collapsed=not self.expand_labels):
					for labels in self.metric.labels:
						yield Static(str(labels))

	def on_collapsible_collapsed(self, event: Collapsible.Collapsed) -> None:
		"""Synchronise expand_labels state"""
		self.expand_labels = False

	def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
		"""Synchronise expand_labels state"""
		self.expand_labels = True


class PromlsVisApp(App):
	"""A Textual app to visualize Prometheus Metrics."""

	TITLE = "Promls"
	CSS_PATH = "promls.css"

	# Add inline CSS for labels container height constraint
	CSS = """
	.labels-scroll {
		max-height: 33vh;
	}
	"""

	BINDINGS = [
		Binding("ctrl+f", "find", "find", priority=True),
		Binding("ctrl+g", "goto", "goto", priority=True),
		Binding("ctrl+e", "errors", "Errors", show=False),
		Binding("greater_than_sign", "expand_all", "Expand all", show=False),
		Binding("less_than_sign", "collapse_all", "Collapse all", show=False),
	]

	def __init__(self, metrics: MetricsTree, errors: list[ParseError], query: str, predicate_factory: PredicateFactory, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.metrics = metrics
		self.errors = errors
		self.query_str = query
		self.predicate_factory = predicate_factory

	def compose(self) -> ComposeResult:
		"""Textual compose"""
		yield Header()
		yield Tree("Prometheus Metrics")
		yield MetricInfoBox()
		yield FindBox(placeholder="Find...", id="find-box")
		yield Footer()
		if self.errors:
			self.notify(f"Warning: {len(self.errors)} parse errors. use `ctrl+e` to show errors", severity="warning")

	def on_mount(self) -> None:
		"""Textual on_mount"""
		self.load_metrics()
		self.focus_findbox()

	def focus_findbox(self):
		"""Focus the find box."""
		self.query_one(FindBox).focus()

	def on_input_changed(self, event: Input.Changed) -> None:
		"""Filter the tree when the query changes."""
		self.query_str = event.value
		self.load_metrics()

	async def action_find(self) -> None:
		"""Filter with `filter_any`"""
		self.predicate_factory = lambda s: filter_any(re.compile(s))
		self.load_metrics()
		self.focus_findbox()

	async def action_goto(self):
		"""Filter with `filter_name`"""
		self.predicate_factory = lambda s: filter_name(re.compile(s))
		self.load_metrics()
		self.focus_findbox()

	def action_expand_all(self) -> None:
		"""Expand all nodes in the tree."""
		tree = self.query_one(Tree)
		tree.root.expand_all()

	def action_collapse_all(self) -> None:
		"""Collapse all nodes in the tree."""
		tree = self.query_one(Tree)
		tree.root.collapse_all()

	def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
		"""Handle node selection in the tree."""
		text_area = self.query_one(MetricInfoBox)
		node = event.node

		if hasattr(node, "data"):
			data = node.data
			text_area.metric = data
		else:
			text_area.metric = None

	def _add_node(self, parent_node, m: TreeT | Metric):
		if isinstance(m, Metric):
			new_node = parent_node.add_leaf(m.name)
			new_node.data = m
		else:
			for k, v in m.items():
				if k == "__value__":
					self._add_node(parent_node, v)
				else:
					self._add_node(parent_node.add(k), v)

	def load_metrics(self):
		"""Load metrics into the tree."""
		tree = self.query_one(Tree)
		tree.clear()
		root = tree.root

		if self.query_str:
			filtered = self.metrics.filter(self.predicate_factory(self.query_str))
		else:
			filtered = self.metrics
		self._add_node(root, paths_to_tree(filtered.metrics, sep="_"))

		root.expand_all()

	def action_errors(self):
		"""Show errors modal."""
		if not self.errors:
			self.notify("No errors to show", severity="information")
			return
		self.push_screen(ErrorsModal(self.errors))
