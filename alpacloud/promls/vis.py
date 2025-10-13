import re

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Input, Label, Static, Tree

from alpacloud.promls.filter import MetricsTree, filter_any
from alpacloud.promls.metrics import Metric
from alpacloud.promls.util import paths_to_tree


class FindBox(Input):
	"""A widget to search for a node in the tree."""

	BINDINGS = [
		("enter", "search('forward')", "Search forward"),
		("pageup", "search('backward')", "Search backward"),
		("pagedown", "search('forward')", "Search forward"),
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


class PromlsVisApp(App):
	"""A Textual app to visualize Prometheus Metrics."""

	TITLE = "Promls"

	CSS_PATH = "promls.css"

	def __init__(self, metrics: MetricsTree, query: str, *args, **kwargs):
		self.metrics = metrics
		self.query = query
		super().__init__(*args, **kwargs)

	def compose(self) -> ComposeResult:
		yield Header()
		yield Tree("Prometheus Metrics")
		yield MetricInfoBox()
		yield FindBox(placeholder="Find...", id="find-box")
		yield Footer()

	def on_mount(self) -> None:
		self.load_metrics(self.metrics)

	def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
		"""Handle node selection in the tree."""
		text_area = self.query_one(MetricInfoBox)
		node = event.node

		if hasattr(node, "data"):
			data = node.data
			text_area.metric = data
		else:
			text_area.metric = None

	def _add_node(self, parent_node, m: MetricsTree | Metric):
		if isinstance(m, Metric):
			new_node = parent_node.add(m.name)
			new_node.data = m
		else:
			for k, v in m.items():
				self._add_node(parent_node.add(k), v)

	def load_metrics(self, metrics: MetricsTree):
		tree = self.query_one(Tree)
		tree.clear()
		root = tree.root

		filtered = metrics.filter(filter_any(re.compile(self.query)))
		self._add_node(root, paths_to_tree(filtered.metrics, sep="_"))

		root.expand_all()
