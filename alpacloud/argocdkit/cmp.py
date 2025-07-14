import json
import os
import sys
from abc import ABC, abstractmethod
try:
	from builtins import ExceptionGroup
except ImportError:
	from exceptiongroup import ExceptionGroup  # remove when we drop 3.10
from typing import Any, TypeVar, Generic

from pydantic import BaseModel, ValidationError
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


def load_params() -> str:
	return json.loads(os.environ["ARGOCD_APP_PARAMETERS"]) or {}


def load_plugin_env() -> dict[str, str]:
	return {k:v for k,v in os.environ.items() if k.startswith("ARGOCD_ENV")}


class CMP(ABC, Generic[S, T]):
	""""""
	@abstractmethod
	def generate(self, app: App, params: T, plugin_env: S) -> str:
		"""Run your plugin."""

	def parse_params(self, params: JSONT) -> T | None:
		def deserialise_param(p: dict):
			if "string" in p:
				return p["string"]
			elif "map" in p:
				return p["map"]
			elif "array" in p:
				return p["array"]
			else:
				raise ValidationError("unknown parameter type")

		return {p["name"]: deserialise_param(p) for p in params}

	def parse_env(self, env: JSONT) -> S:
		return env

	def run(self, app: App, params: JSONT, plugin_env: JSONT):
		"""Entrypoint for running a plugin."""
		errors = []

		try:
			loaded_plugin = self.parse_params(params)
		except ValidationError as e:
			errors.append(e)

		try:
			loaded_plugin_env = self.parse_env(plugin_env)
		except ValidationError as e:
			errors.append(e)

		if errors:
			raise ExceptionGroup("error loading parameters for plugin", errors)

		generated = self.generate(app, loaded_plugin, loaded_plugin_env)
		return generated


def run_cmp(cmp: CMP[S, T]):
	app = App()
	params = load_params()
	plugin_env = load_plugin_env()

	generated = cmp.run(app, params, plugin_env)
	print(generated, file=sys.stdout)