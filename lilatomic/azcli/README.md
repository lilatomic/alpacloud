# Ansible Collection - lilatomic.azcli

Run azure-cli tasks from Ansible

## Usage

It's really simple.

It's basically just serialising the `az` command. For example, `az group create --name TutorialResources --location eastus` becomes:

```yaml+jinja2
- name: create resource group
  lilatomic.azcli.cli:
    cmd: group create
    args:
      name: TutorialResources
      location: eastus
```

This module does a few things to make this even simpler:
1. automatically adds the leading dashes
2. accepts short args too (eg 'resource-group' or 'g')
3. automatically deserialises the result

## Rationale

There are a few ways that the module makes things easier than using the `command` module to run `az`:
1. no need to quote arguments. multi-word arguments are parsed correctly automatically
2. automatically parses the output JSON and makes it available in the return value
3. output format is always set to JSON. Some people may configure their default output format to something other than JSON (like `table`), which makes parsing the output JSON unreliable without always adding `-o json`
4. composability of arguments: you can easily merge common arguments by just merging dictionaries normally
