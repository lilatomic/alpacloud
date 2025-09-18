import functools


def compose(*funcs):
	return functools.reduce(lambda f, g: lambda x: f(g(x)), funcs)
