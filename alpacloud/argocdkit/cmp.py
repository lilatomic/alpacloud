import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from alpacloud.argocdkit.spec import Plugin

if sys.version_info >= (3, 11):
	from builtins import ExceptionGroup  # type: ignore
else:
	from exceptiongroup import ExceptionGroup  # remove when we drop 3.10
from typing import Any, Generic, TypeVar

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from alpacloud.lens.util.type import JSONT

S = TypeVar("S")
T = TypeVar("T")


class App(BaseSettings):
	name: str
	namespace: str
	project_name: str
	revision: str
	revision_short: str
	revision_short_8: str
	source_path: str
	source_repo_url: str
	source_target_revision: str

	model_config = SettingsConfigDict(env_prefix="ARGOCD_APP_")


def load_params(environ=os.environ) -> list[dict[str, Any]]:
	return json.loads(environ["ARGOCD_APP_PARAMETERS"]) or []


def load_plugin_env(environ=os.environ) -> dict[str, str]:
	return {k.removeprefix("ARGOCD_ENV_"): v for k, v in environ.items() if k.startswith("ARGOCD_ENV")}


class CMP(ABC, Generic[S, T]):
	""""""

	@property
	@abstractmethod
	def spec(self) -> Plugin:
		"""The ArgoCD plugin spec."""

	@abstractmethod
	def generate(self, app: App, params: T, plugin_env: S) -> str:
		"""Run your plugin."""

	def parse_params(self, params: list[dict[str, Any]]) -> T:
		def deserialise_param(p: JSONT):
			assert isinstance(p, dict)
			if "string" in p:
				return p["string"]
			elif "map" in p:
				return p["map"]
			elif "array" in p:
				return p["array"]
			else:
				raise ValidationError("unknown parameter type")

		return {p["name"]: deserialise_param(p) for p in params}  # type: ignore

	def parse_env(self, env: JSONT) -> S:
		return env  # type: ignore

	def run(self, app: App, params: list[dict[str, Any]], plugin_env: JSONT) -> str:
		"""Entrypoint for running a plugin."""
		errors = []

		try:
			loaded_plugin = self.parse_params(params)
		except Exception as e:
			errors.append(e)

		try:
			loaded_plugin_env = self.parse_env(plugin_env)
		except Exception as e:
			errors.append(e)

		if errors:
			raise ExceptionGroup("error loading parameters for plugin", errors)

		generated = self.generate(app, loaded_plugin, loaded_plugin_env)
		return generated


def run_cmp(cmp: CMP[S, T]):
	app = App()
	params = load_params()
	plugin_env = load_plugin_env()

	generated = cmp.run(app, params, plugin_env)  # type: ignore
	print(generated, file=sys.stdout)


def entrypoint(cmp: CMP):
	def _entrypoint():
		if len(sys.argv) > 1 and sys.argv[1] == "gen-cfg":
			if len(sys.argv) > 2:
				p = Path(sys.argv[2])
			else:
				p = Path("/home/argocd/cmp-server/config/plugin.yaml")
			p.parent.mkdir(parents=True, exist_ok=True)
			with p.open(mode="w") as f:
				f.write(cmp.spec.model_dump_json())
		else:
			run_cmp(cmp)

	return _entrypoint
