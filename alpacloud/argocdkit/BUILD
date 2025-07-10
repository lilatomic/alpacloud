python_sources()

docker_image(
	name="docker",
	repository="cmp",
)

python_tests(
	name="tests",
)

pex_binary(
	name="__main__",
	entry_point="__main__.py",
	interpreter_constraints=["CPython==3.13.*"],
#	shebang="/usr/bin/env python3",
)