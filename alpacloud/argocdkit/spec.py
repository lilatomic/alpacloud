from dataclasses import field
from typing import Literal

from pydantic import BaseModel


class Command(BaseModel):
	command: list[str]
	args: list[str] = field(default_factory=list)


class Spec(BaseModel):
	version: str
	init: Command | None = None
	generate: Command | None = None
	# discover: ???
	# parameters: ???
	preserveFileMode: bool = False
	provideGitCreds: bool = False


class Metadata(BaseModel):
	name: str


class Plugin(BaseModel):
	metadata: Metadata
	spec: Spec
	apiVersion: Literal["argoproj.io/v1alpha1"] = "argoproj.io/v1alpha1"
	kind: Literal["ConfigManagementPlugin"] = "ConfigManagementPlugin"
