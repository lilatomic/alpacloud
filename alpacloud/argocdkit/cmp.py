import os
import sys
from abc import ABC, abstractmethod
from builtins import ExceptionGroup
from typing import Any, TypeVar, Generic

from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

S = TypeVar("S", bound=BaseModel)
T = TypeVar("T", bound=BaseModel)


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

class Params(BaseSettings):
	parameters: dict[str, Any]

	model_config = SettingsConfigDict(env_prefix="ARGOCD_APP_")


def load_plugin_env() -> dict[str, str]:
	return {k:v for k,v in os.environ.items() if k.startswith("ARGOCD_ENV")}


class CMP(ABC, Generic[S, T]):
	""""""
	param_t: type[T]
	env_t: type[S]

	@abstractmethod
	def generate(self, app: App, params: T, plugin_env: S) -> str:
		"""Run your plugin."""

	def run(self, app: App, params: Params, plugin_env: dict[str, str]):
		"""Entrypoint for running a plugin."""
		errors = []

		try:
			loaded_plugin = self.param_t.model_validate(params)
		except ValidationError as e:
			errors.append(e)

		try:
			loaded_plugin_env = self.env_t.model_validate(plugin_env)
		except ValidationError as e:
			errors.append(e)

		if errors:
			raise ExceptionGroup("error loading parameters for plugin", errors)

		generated = self.generate(app, loaded_plugin, loaded_plugin_env)
		return generated


def run_cmp(cmp: CMP[S, T]):
	app = App()
	params = Params()
	plugin_env = load_plugin_env()

	generated = cmp.run(app, params, plugin_env)
	print(generated, file=sys.stdout)