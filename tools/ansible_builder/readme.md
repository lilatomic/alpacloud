# alpacloud-ansible-builder

This tool automatically builds and installs Ansible Collections.

This is useful for testing out purpose built collections. It's also nice for testing collections. I think it's most useful for repositories with collections alongside deployments:

```
- collections
	- our_monitoring
- deployments
	- our_monitoring_staging
	- our_monitoring_team_0
	- our_monitoring_team_1
	- our_monitoring_team_2
```

## usage

The Ansible builder can be used to build all collections in a directory:

```shell
alpacloud-ansible-builder .
```

It can also be used to watch collections for changes and rebuild them.

```shell
alpacloud-ansible-builder --watch .
```

The `--debounce` option lets you customise the time between the last change happening to a collection and a build being triggered.
