import enum
import re

import click

from alpacloud.promls.fetch import Parser, FetcherURL
from alpacloud.promls.filter import MetricsTree, filter_name


class PrintMode(enum.StrEnum):
	flat = "flat"
	tree = "tree"
	full = "full"

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


def do_print(tree: MetricsTree, mode: PrintMode):
	"""Format and print identified metrics."""

	match mode:
		case PrintMode.flat:
			txt = "\n".join(k for k, v in tree.metrics.items())
		case _:
			txt = "halp"
	click.echo(txt)


@click.group()
def search():
	"""Search metrics"""


@search.command()
@common_args()
def name(url, filter: str,
		 display: PrintMode,
		 ):
	tree = do_fetch(url)
	filtered = tree.filter(filter_name(re.compile(filter)))
	do_print(filtered, display)
