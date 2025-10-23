import enum
import itertools
import json
import re

import click

from alpacloud.promls.fetch import FetcherURL, Parser
from alpacloud.promls.filter import MetricsTree, filter_any, filter_ish, filter_name, filter_path
from alpacloud.promls.metrics import Metric
from alpacloud.promls.util import paths_to_tree
from alpacloud.promls.vis import PromlsVisApp


class PrintMode(enum.StrEnum):
	flat = "flat"
	tree = "tree"
	full = "full"
	json = "json"

	@staticmethod
	def parse(ctx, param, value):
		# Normalize and map to the enum so command handlers receive PrintMode
		if value is None:
			return None
		return PrintMode(value.lower())


arg_url = click.argument("url")
opt_mode = click.option(
	"--display",
	type=click.Choice([m.value for m in PrintMode], case_sensitive=False),
	callback=PrintMode.parse,
	default=PrintMode.flat.value,
	show_default=True,
	help=f"Display mode: {', '.join(m.value for m in PrintMode)}",
)
opt_filter = click.option("--filter")


def common_args():
	def decorator(f):
		f = opt_filter(f)
		f = opt_mode(f)
		f = arg_url(f)
		return f

	return decorator


def do_fetch(url: str):
	return MetricsTree(Parser().parse(FetcherURL(url).fetch()))


def mk_indent(i: int, s: str) -> str:
	return "\t" * i + s


def render_metric(m: Metric) -> str:
	return f"{m.name} ({m.type}) {m.help or ''}"


def _print_nested(tree, indent=0) -> list[tuple[int, str]]:
	o: list[tuple[int, str]] = []  # prevents this being accidentally quadratic

	for k, v in tree.items():
		if k == "__value__":
			o.append((indent, render_metric(v)))
		else:
			if isinstance(v, Metric):
				o.append((indent, f"{k} : {render_metric(v)}"))
			else:
				o.append((indent, k))
				o.extend(_print_nested(v, indent + 1))

	return o


def do_print(tree: MetricsTree, mode: PrintMode):
	"""Format and print identified metrics."""

	match mode:
		case PrintMode.flat:
			txt = "\n".join([render_metric(v) for v in tree.metrics.values()])
		case PrintMode.full:
			metric_text = [[f"# HELP {v.name} {v.help}", f"# TYPE {v.name} {v.type}", v.name] for v in tree.metrics.values()]
			txt = "\n".join(itertools.chain.from_iterable(metric_text))
		case PrintMode.tree:
			as_tree = paths_to_tree(tree.metrics, sep="_")
			for_printing = _print_nested(as_tree)
			txt = "\n".join([mk_indent(i, s) for i, s in for_printing])
		case PrintMode.json:
			txt = json.dumps({k: v.__dict__ for k, v in tree.metrics.items()}, indent=2)
	click.echo(txt)


@click.group()
def search():
	"""Search metrics"""


@search.command()
@common_args()
def name(url, filter: str, display: PrintMode):
	"""Filter metrics by their name"""
	tree = do_fetch(url)
	filtered = tree.filter(filter_name(re.compile(filter)))
	do_print(filtered, display)


@search.command()
@common_args()
def any(url, filter: str, display: PrintMode):
	"""Filter metrics by any of their properties"""
	tree = do_fetch(url)
	filtered = tree.filter(filter_any(re.compile(filter)))
	do_print(filtered, display)


@search.command()
@common_args()
def path(url, filter: str, display: PrintMode):
	"""Filter metrics by their path"""
	tree = do_fetch(url)
	filtered = tree.filter(filter_path(filter.split("_")))
	do_print(filtered, display)


@search.command()
@common_args()
def ish(url, filter: str, display: PrintMode):
	"""Filter metrics using a fuzzy match"""
	tree = do_fetch(url)
	filtered = tree.filter(filter_ish(filter))
	do_print(filtered, display)


@search.command()
@arg_url
@opt_filter
def browse(url, filter: str):
	"""Browse metrics in an interactive visualizer"""
	real_filter = filter or ".*"
	PromlsVisApp(do_fetch(url), real_filter, lambda s: filter_any(re.compile(s))).run()
