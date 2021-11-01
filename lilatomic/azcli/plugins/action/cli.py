from dataclasses import dataclass, field

import io
import itertools
import json
from ansible.plugins.action import ActionBase
from azure.cli.core import get_default_cli, AzCli
from knack.util import CommandResultItem
from typing import Dict, TypeVar

A = TypeVar('A')


@dataclass
class AzCliParams:
	cmd: str
	args: Dict[str, str] = field(default_factory=dict)
	output: str = "json"

	def as_cmd(self):
		command = self.cmd.split(' ')
		arg_statements = []
		for k, v in self.args.items():
			arg_statements.append(self._cli_format_arg(k))
			arg_statements.append(v)
		return list(itertools.chain(
			command,
			arg_statements,
			['--output', self.output],
			))

	@staticmethod
	def _cli_format_arg(arg: str):
		if arg.startswith('--') or arg.startswith('-'):  # dashes have been specified by the user
			return arg
		elif len(arg) == 1:  # single letters get 1 dash
			return '-' + arg
		else:
			return '--' + arg


class ActionModule(ActionBase):

	def run(self, tmp=None, task_vars=None):
		super().run(tmp=tmp, task_vars=task_vars)
		ret = {}

		args = AzCliParams(**self._task.args)

		cli: AzCli = get_default_cli()

		out_buffer = io.StringIO("")

		try:
			exit_code = cli.invoke(args=args.as_cmd(), out_file=out_buffer)
		except SystemExit as e:
			if e.code == 2:
				exit_code = 2
				ret["failed"] = True
			else:
				raise
		if exit_code != 0:
			ret["failed"] = True
		ret["cli_result"] = self._serialise_command_result_item(cli.result)
		if cli.result.error:
			ret["error"] = str(cli.result.error)

		out_buffer.seek(0)
		cli_output = out_buffer.read()

		ret.update(self.parse_output(cli_output, output_format=args.output))

		return ret

	@staticmethod
	def _serialise_command_result_item(i: CommandResultItem):
		error = ActionModule._repr_or_pass(i.error)
		raw_result = ActionModule._repr_or_pass(i.raw_result)
		return {
			'result': i.result,
			'exit_code': i.exit_code,
			'error': error,
			'raw_result': raw_result
			}

	@staticmethod
	def _repr_or_pass(x):
		"""force item to be JSON serialiasable by invoking repr or returning"""
		if hasattr(x, "__repr__"):
			return x.__repr__()
		else:
			return x

	@staticmethod
	def parse_output(cli_output, output_format):
		ret = {}
		if len(cli_output) > 0:
			if output_format == "json":
				parsed_cli_output = json.loads(cli_output)
				if isinstance(parsed_cli_output, dict):
					ret.update(parsed_cli_output)
				elif isinstance(parsed_cli_output, list):
					ret.update(enumerate(parsed_cli_output))
				else:
					ret["output"] = parsed_cli_output
			else:
				ret["output"] = cli_output
		return ret
