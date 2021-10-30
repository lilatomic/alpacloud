import json

import io
from dataclasses import dataclass, fields, field

import itertools
from ansible.plugins.action import ActionBase
from azure.cli.core import get_default_cli, AzCli
from typing import List, Dict, TypeVar, Type, Tuple

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

		out_buffer.seek(0)
		cli_output = out_buffer.read()
		if len(cli_output) > 0:
			ret.update(json.loads(cli_output))

		return ret