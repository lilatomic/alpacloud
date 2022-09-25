import json

import pytest
from lilatomic.azcli.plugins.action.cli import ActionModule, AzCliParams


def _assert_arg_has_value(cmd, arg, value, normalise=True):
	if normalise:
		normalised_arg_name = AzCliParams._cli_format_arg(arg)
	else:
		normalised_arg_name = arg
	index_k = cmd.index(normalised_arg_name)
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

	expected = ["command", "verb", "--k1", "v1", "--k2", "v2", "--output", "json"]
	assert cmd == expected


def test__AzCliParams__without_args():
	p = AzCliParams("command")

	cmd = p.as_cmd()

	assert cmd[0] == "command"
	_assert_arg_has_value(cmd, "output", "json")


def test__AzCliParams__output():
	p = AzCliParams("command", output="yaml")

	cmd = p.as_cmd()

	_assert_arg_has_value(cmd, "output", "yaml")


@pytest.mark.parametrize(
	'argname, expected', [
		('s', '-s'),
		('-s', '-s'),
		('long', '--long'),
		('--long', '--long')
	]
)
def test__AzClidParams__format_args(argname, expected):
	p = AzCliParams("command", args={argname: 'value'})

	cmd = p.as_cmd()

	_assert_arg_has_value(cmd, expected, 'value', normalise=False)


@pytest.mark.parametrize(
	"cli_output,output_format,expected",
	[
		(json.dumps({}), "json", {}),
		(json.dumps({'a': 1}), "json", {'a': 1}),
		(json.dumps(['a', 'b']), "json", {0: 'a', 1: 'b'}),
		(json.dumps(1), "json", {'output': 1}),
		('', "json", {}),
		("some\noutput", "table", {'output': "some\noutput"})
	]
)
def test__parse_output(cli_output, output_format, expected):
	assert expected == ActionModule.parse_output(cli_output, output_format)
