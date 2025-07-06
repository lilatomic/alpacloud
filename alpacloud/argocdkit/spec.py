from dataclasses import dataclass
from typing import Literal


@dataclass
class Command:
	command: list[str]
	args: list[str]


@dataclass
class Spec:
	version: str
	init: Command
	generate: Command
	# discover: ???
	# parameters: ???
	preserveFileMode: bool = False
	provideGitCreds: bool = False



@dataclass
class Metadata:
	name: str


@dataclass
class Plugin:
	metadata: Metadata
	spec: Spec
	apiVersion: Literal["argoproj.io/v1alpha1"] = "argoproj.io/v1alpha1"
	kind: Literal["ConfigManagementPlugin"] = "ConfigManagementPlugin"
