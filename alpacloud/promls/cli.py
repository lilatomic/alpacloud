"""CLI interface for promls."""

import enum
import itertools
import json
import re

import click

from alpacloud.promls.fetch import Collector, FetcherURL, ParseError, Parser
from alpacloud.promls.filter import MetricsTree, filter_any, filter_name, filter_path
from alpacloud.promls.metrics import Metric
from alpacloud.promls.util import paths_to_tree
from alpacloud.promls.vis import PromlsVisApp


class PrintMode(enum.StrEnum):
	"""Output format"""

	flat = "flat"
	tree = "tree"
	full = "full"
	json = "json"

	@staticmethod
	def parse(ctx, param, value):
		"""Parse from click"""
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
opt_combine = click.option(
	"--combine-submetrics",
	is_flag=True,
	help="Combine submetrics into their parent. For example, combine a histogram's `sum` and `count` into the main histogram metric.",
	default=True,
)


def common_args():
	"""Common arguments for search commands"""

	def decorator(f):
		f = opt_filter(f)
		f = opt_mode(f)
		f = arg_url(f)
		f = opt_combine(f)
		return f

	return decorator


def do_fetch(url: str, combine_submetrics: bool):
	"""Do the fetch and parse."""
	lines, errors = Parser.parse_all(FetcherURL(url).fetch())
	values = Collector(lines, combine_submetrics).assemble()

	return MetricsTree({e.name: e for e in values}), errors


def mk_indent(i: int, s: str) -> str:
	"""Indent a line"""
	return "\t" * i + s


def render_metric(m: Metric) -> str:
	"""Render a metric in a human-readable format."""
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
	return txt


def print_errors(errors: list[ParseError]):
	"""Print parse errors"""
	if not errors:
		return
	click.echo(f"warning: parse errors: {len(errors)}", err=True)
	for err in errors:
		click.echo(str(err), err=True)


@click.group()
def search():
	"""Search metrics"""


@search.command()
@common_args()
def name(url, filter: str, display: PrintMode, combine_submetrics: bool):
	"""Filter metrics by their name"""
	tree, errors = do_fetch(url, combine_submetrics)
	print_errors(errors)
	filtered = tree.filter(filter_name(re.compile(filter)))
	click.echo(do_print(filtered, display))


@search.command()
@common_args()
def any(url, filter: str, display: PrintMode, combine_submetrics: bool):
	"""Filter metrics by any of their properties"""
	tree, errors = do_fetch(url, combine_submetrics)
	print_errors(errors)
	filtered = tree.filter(filter_any(re.compile(filter)))
	click.echo(do_print(filtered, display))


@search.command()
@common_args()
def path(url, filter: str, display: PrintMode, combine_submetrics: bool):
	"""Filter metrics by their path"""
	tree, errors = do_fetch(url, combine_submetrics)
	print_errors(errors)
	filtered = tree.filter(filter_path(filter.split("_")))
	click.echo(do_print(filtered, display))


@search.command()
@arg_url
@opt_filter
@opt_combine
def browse(url, filter: str, combine_submetrics: bool):
	"""Browse metrics in an interactive visualizer"""
	real_filter = filter or ".*"
	results, errors = do_fetch(url, combine_submetrics)
	PromlsVisApp(results, errors, real_filter, lambda s: filter_any(re.compile(s))).run()
