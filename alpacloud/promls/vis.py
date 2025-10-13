import re

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Input, Tree

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
		yield FindBox(placeholder="Find...", id="find-box")
		yield Footer()

	def on_mount(self) -> None:
		self.load_metrics(self.metrics)

	def _add_node(self, parent_node, m: MetricsTree | Metric):
		if isinstance(m, Metric):
			parent_node.add(m.name)
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
