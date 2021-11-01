#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = """
---
module: cli
short_description: Run azure-cli tasks from Ansible
description:
  - An easy way to use the [azure cli](https://docs.microsoft.com/en-us/cli/azure/) 
version_added: "0.1.0"
author:
  - Daniel Goldman <danielgoldman4@gmail.com>
options:
  cmd:
    description: The az-cli command to run
    required: true
    type: string
  arg:
    description: arguments to the command. leading dashes will be automatically prepended
    required: false
    default: {}
    type: dict
  output:
    description: the output format to use
    required: false
    default: json
    type: str
"""

EXAMPLES = """
---
- name: command without arguments
  lilatomic.azcli.cli:
    cmd: account show
  register: account_show

- name: command with arguments
  lilatomic.azcli.cli:
    cmd: account set
    args:
      s: "{{ account_show['id'] }}"

- name: create resource group
  lilatomic.azcli.cli:
    cmd: group create
    args:
      name: TutorialResources
      location: eastus
"""

RETURN = """
---
root:
  description: elements of the JSON response are added as attributes of the root node. If returned JSON is a list, these will be under numerical keys
  returned: when output == json (default)
  type: complex
output:
  description: the output of the command
  returned: when output != json or output is a scalar (not a list or dict)
  type: str
error:
  description: error of the CLI invocation
  returned: when failed due to CLI invocation
  type: complex
"""
