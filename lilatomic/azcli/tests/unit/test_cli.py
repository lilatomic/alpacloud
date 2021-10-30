from typing import List

from plugins.action.cli import ActionModule, AzCliParams


def _assert_arg_has_value(cmd, arg, value):
	index_k = cmd.index(arg)
	assert index_k != -1, f"arg {arg} not found"
	v = cmd[index_k + 1]
	assert v == value


def test__AzCliParams__as_cmd():
	p = AzCliParams(
			cmd="command verb",
			args={
				'k1': 'v1',
				'k2': 'v2'
				}
		)

	cmd = p.as_cmd()

	assert isinstance(cmd, list)

	expected = ["command", "verb", "k1", "v1", "k2", "v2", "--output", "json"]
	assert cmd == expected
