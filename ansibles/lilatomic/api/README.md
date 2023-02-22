# Ansible Collection - lilatomic.api

A collection for better handling of API connections

## Contents

## HTTP Action Plugins

Note that these only run on the controller

- http : general-purpose HTTP action plugin
- delete, get, patch, post, put : shortcuts for that HTTP verb

They're pretty zippy too.

| site                               | uri       | lilatomic.api | speedup |
| ---------------------------------- | --------- | ------------- | ------- |
| https://httpbingo.org              | 1.0 req/s | 4.3 req/s     | 4.3     |
| `python3 -m http.server` localhost | 2.0 req/s | 21.2 req/s    | 10.7    |

## License

Ansible Galaxy complained that Round Robin isn't in the SPDX, so you can also choose the SSPL if you like reading
