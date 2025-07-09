import sys

from alpacloud.argocdkit.spec import Plugin, Metadata, Spec, Command

cmp_helm = Plugin(
	metadata=Metadata(name="helm-and-python"),
	spec=Spec(
		version="0.0.1",
		generate=Command(
			command=["helm", "template"],
		),
	)
)

if __name__ == "__main__":
	print(cmp_helm.model_dump_json(), file=sys.stdout)