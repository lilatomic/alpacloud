python_sources()

docker_image(
	name="docker",
	repository="cmp",
	image_tags=["0.0.1"],
)

python_tests(
	name="tests",
	dependencies=["./test_resources:k8s_objs"],
	runtime_package_dependencies=["./test_resources:my_postrenderer"],
)

pex_binary(
	name="__main__",
	entry_point="__main__.py",
	interpreter_constraints=["CPython==3.13.*"],
#	shebang="/usr/bin/env python3",
)