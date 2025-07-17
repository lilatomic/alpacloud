# ArgoCD Kit

A toolkit for building services for ArgoCD

## Configuration Management Plugins

ArgoCD CMPs let ArgoCD run your code to generate the manifests for Applications. You can use this to run custom templating tools or even implement your own.

1. Create a subclass of `CMP`

```python
from alpacloud.argocdkit.cmp import CMP, App, T, S

class HelmPostRendererCMP(CMP):
    ...
```

1. Define a CMP spec

```python
from alpacloud.argocdkit.spec import Plugin, Metadata, Spec, Command

class HelmPostRendererCMP(CMP):
    @property
    def spec(self) -> Plugin:
        return Plugin(
            metadata=Metadata(name="helm-and-python"),
            spec=Spec(
                version="0.0.1",
                generate=Command(
                    command=["/bin/alpacloud-argocdkit"],  # this is the path to the entrypoint for this file
                ),
            )
)
```

2. Implement the logic of your plugin in the `generate` method. You can also use the hooks `parse_params` and `parse_env` to parse those attributes on the Application's definition into normal Python classes.

3. 
```python
import sh
from pydantic import BaseModel

from alpacloud.argocdkit.cmp import CMP, App, T, S
from alpacloud.lens.util.type import JSONT

class HelmParameters(BaseModel):
	valueFiles: list[str] = []
	valuesObject: dict = {}
	values: str | None = None
	postRenderers: list[str] = []


class HelmPostRendererCMP(CMP):
	def parse_params(self, params: JSONT) -> HelmParameters:
		params = super().parse_params(params)
		return HelmParameters.model_validate(params)

	# helper methods for running Helm

	def generate(self, app: App, params: HelmParameters, plugin_env: S):
		argv = []

		argv.extend(self.values_argv(params.valuesObject, params.values, params.valueFiles))
		argv.append(f"--namespace={app.namespace}")

		argv.extend(self.postrenderers_argv(params.postRenderers))

		return sh.Command("helm")(["template", app.name, ".", *argv])
```

4. Run your plugin on startup

```python
#!/usr/bin/env python3

if __name__ == "__main__":
	entrypoint(HelmPostRendererCMP())()
```

5. To generate the CMP plugin config file, run the cmp with the argument "gen-cfg". This will put it in the correct directory for a container, although you can also specify the output file as the second argument.

```shell
./my_cmp "gen-cfg"
```

6. Register your plugin with ArgoCD following [their documentation](https://argo-cd.readthedocs.io/en/latest/operator-manual/config-management-plugins/#register-the-plugin-sidecar)

## Helm post-renderer

Sometimes a Helm chart doesn't have an option for a feature that you need. You can write a post-renderer to run your code on the rendered files of a Helm chart to do whatever you want. You can convert a `BoundLens` from the `alpacloud.lens` library or any function into a postrederer with the `postrenderer` function.

```python
#!/usr/bin/env python3

from alpacloud.argocdkit.postrender import postrenderer
from alpacloud.lens.k8s import labels
from alpacloud.lens.models import CombinedBoundLens, Const, ForeachLens, korn

p = postrenderer(CombinedBoundLens((
	ForeachLens(labels / korn("my-label")) @ Const("my-label-value"),
)))

if __name__ == "__main__":
	p()
```

```python
#!/usr/bin/env python3

from alpacloud.argocdkit.postrender import postrenderer
from alpacloud.lens.util.type import JSONT

def add_note(manifests: list[JSONT]) -> list[JSONT]:
	for manifest in manifests:
		manifest["metadata"].get("labels", {})["my-label"] = "my-label-value"
	return manifests

p = postrenderer(add_note)

if __name__ == "__main__":
	p()
```