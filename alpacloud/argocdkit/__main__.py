import json
import os
import sys
import tempfile
from pathlib import Path

import sh
from pydantic import BaseModel, TypeAdapter

from alpacloud.argocdkit.cmp import run_cmp, CMP, App, T, S
from alpacloud.argocdkit.spec import Plugin, Metadata, Spec, Command
from alpacloud.lens.util.type import JSONT

cmp_spec = Plugin(
	metadata=Metadata(name="helm-and-python"),
	spec=Spec(
		version="0.0.1",
		generate=Command(
			command=["/bin/alpacloud-argocdkit"],
		),
	)
)

class HelmParameters(BaseModel):
	valueFiles: list[str] = []
	valuesObject: dict = {}
	values: str | None = None


class HelmPostRendererCMP(CMP):
	def parse_params(self, params: JSONT) -> T:
		return HelmParameters.model_validate(params)

	def values_argv(self, valuesObject, values, valueFiles):
		values_files = valueFiles

		if values:
			values_file = tempfile.TemporaryFile(mode="w", prefix="values-", suffix=".json")
			with values_file.open("w") as f:
				f.write(json.dumps(valuesObject))
			values_files.append(values_file.name)

		if valuesObject:
			values_object_file = tempfile.TemporaryFile(mode="w", prefix="values-object-", suffix=".json")
			with values_object_file.open("w") as f:
				f.write(json.dumps(valuesObject))
			values_files.append(values_object_file.name)

		return [f"--values={f}" for f in valueFiles]


	def generate(self, app: App, params: T, plugin_env: S):
		argv = []

		argv.extend(self.values_argv(params.valuesObject, params.values, params.valueFiles))
		argv.append(f"--namespace={app.namespace}")

		return sh.Command("helm")(["template", ".", app.name, *argv])


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1] == "gen-cfg":
		p = Path("/home/argocd/cmp-server/config/plugin.yaml")
		p.parent.mkdir(parents=True, exist_ok=True)
		with p.open(mode="w") as f:
			f.write(cmp_spec.model_dump_json())
	else:
		run_cmp(
			HelmPostRendererCMP()
		)