python_sources()

pex_binary(
	name="my_postrenderer",
	entry_point="my_postrenderer.py",
	interpreter_constraints=["CPython==3.13.*"],
)

files(
	name="k8s_objs",
	sources=["**/*.yml", "**/*.yaml", "**/*.tpl", "**/*.json"],
)

docker_image(
	name="docker",
	repository="cmp",
	image_tags=["latesttest"],
)
