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
