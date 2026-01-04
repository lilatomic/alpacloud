import re

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Collapsible, Footer, Header, Input, Label, Static, Tree

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
		self.clear()


class MetricInfoBox(Widget):
	"""A widget to display information about the selected Metric."""

	metric: Reactive[Metric | None] = reactive(None, recompose=True)

	def compose(self) -> ComposeResult:
		with Vertical():
			if not self.metric:
				yield Label("Metric Info")
			else:
				with Horizontal():
					yield Container(Label(self.metric.name, variant="accent"), classes="left")
					yield Container(Label(self.metric.type, variant="accent"), classes="right")
				yield Static(self.metric.help)

				with Collapsible(title="Labels"):
					for labels in self.metric.labels:
						yield Static(str(labels))


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
		Binding("greater_than_sign", "expand_all", "Expand all", show=False),
		Binding("less_than_sign", "collapse_all", "Collapse all", show=False),
	]

	def __init__(self, metrics: MetricsTree, query: str, predicate_factory: PredicateFactory, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.metrics = metrics
		self.query_str = query
		self.predicate_factory = predicate_factory

	def compose(self) -> ComposeResult:
		yield Header()
		yield Tree("Prometheus Metrics")
		yield MetricInfoBox()
		yield FindBox(placeholder="Find...", id="find-box")
		yield Footer()

	def on_mount(self) -> None:
		self.load_metrics()
		self.focus_findbox()

	def focus_findbox(self):
		self.query_one(FindBox).focus()

	def on_input_changed(self, event: Input.Changed) -> None:
		self.query_str = event.value
		self.load_metrics()

	async def action_find(self) -> None:
		self.predicate_factory = lambda s: filter_any(re.compile(s))
		self.load_metrics()
		self.focus_findbox()

	async def action_goto(self):
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
			new_node = parent_node.add(m.name)
			new_node.data = m
		else:
			for k, v in m.items():
				self._add_node(parent_node.add(k), v)

	def load_metrics(self):
		tree = self.query_one(Tree)
		tree.clear()
		root = tree.root

		if self.query_str:
			filtered = self.metrics.filter(self.predicate_factory(self.query_str))
		else:
			filtered = self.metrics
		self._add_node(root, paths_to_tree(filtered.metrics, sep="_"))

		root.expand_all()
