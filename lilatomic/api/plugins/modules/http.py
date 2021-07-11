#!/usr/bin/python
# -*- coding: utf-8 -*-


DOCUMENTATION = """
---
module: lilatomic.api.http
short_description: A nice and friendly HTTP API
description:
  - An easy way to use the [requests](https://docs.python-requests.org/en/master/) library to make HTTP requests
  - Define connections and re-use them across tasks
version_added: "0.1.0"
options:
  connection:
    description: the name of the connection to use
    required: true
    type: string
  method:
    description: the HTTP method to use
    required: true
    default: GET
    type: string
  path:
    description: the slug to join to the connection's base
  data:
    description: object to send in the body of the request.
    required: false
    type: string or dict
  json:
    description: json data to send in the body of the request.
    required: false
    type: string or dict
  headers:
    description: HTTP headers for the request
    required: false
    type: dict
    default: dict()
  status_code:
    description: acceptable status codes
    required: false
    default: requests default, status_code < 400
    type: list
    elements: int
  timeout:
    description: timeout in seconds of the request
    required: false
    default: 15
    type: float
  log_request:
    description: returns information about the request. Useful for debugging. Censors Authorization header unless log_auth is used.
    required: false
    default: false
    type: bool
  log_auth:
    description: uncensors the Authorization header.
    required: false
    default: false
    type: bool
  kwargs:
    description: Access hatch for passing kwargs to the requests.request method. Recursively merged with and overrides kwargs set on the connection.
    required: false
    default: None
    type: dict
"""

EXAMPLES = """
---
- name: post
  lilatomic.api.http:
    connection: httpbin
    method: POST
    path: /post
    data:
      1: 1
      2: 2
  vars:
    lilatomic_api_http:
      httpbin:
        base: "https://httpbingo.org/"

- name: GET with logging of the request
  lilatomic.api.http:
    connection: fishbike
    path: /
    log_request: true
  vars:
    lilatomic_api_http:
      httpbin:
        base: "https://httpbingo.org/"

- name: GET with Bearer auth
  lilatomic.api.http:
    connection: httpbin_bearer
    path: /bearer
    log_request: true
    log_auth: true
  vars:
    lilatomic_api_http:
      httpbin_bearer:
        base: "https://httpbin.org"
        auth:
          method: bearer
          token: hihello

- name: Use Kwargs for disallowing redirects
  lilatomic.api.http:
    connection: httpbin
    path: redirect-to?url=get
    kwargs:
      allow_redirects: false
    status_code: [ 302 ]
  vars:
    lilatomic_api_http:
      httpbin:
        base: "https://httpbingo.org/"
"""

RETURN = """
---
json:
  description: json body
  returned: response has headers Content-Type == "application/json"
  type: complex
  sample: {
    "authenticated": true,
    "token": "hihello"
  }
content:
  description: response.content
  returned: always
  type: str
  sample: |
    {\\n  "authenticated": true, \\n  "token": "hihello"\\n}\\n
msg:
  description: response body
  returned: always
  type: str
  sample: |
    {\\n  "authenticated": true, \\n  "token": "hihello"\\n}\\n
content-length:
  description: response Content-Length header
  returned: always
  type: int
  sample: 51
content-type:
  description: response Content-Type header
  returned: always
  type: string
  sample: "application/json"
cookies:
  description: the cookies from the response
  returned: always
  type: dict
  sample: { }
date:
  description: response Date header
  returned: always
  type: str
  sample: "Sat, 10 Jul 2021 23:14:14 GMT"
elapsed:
  description: seconds elapsed making the request
  returned: always
  type: int
  sample: 0
redirected:
  description: if response was redirected
  returned: always
  type: bool
  sample: false
server:
  description: response Server header
  returned: always
  type: str
  sample: "gunicorn/19.9.0"
status:
  description: response status code; alias for status_code
  returned: always
  type: str
  sample: 200
url:
  description: the URL from the response
  returned: always
  type: str
  sample: "https://httpbin.org/bearer"
encoding:
  description: response encoding
  returned: always
  type: str
  sample: "utf-8"
headers:
  description: response headers
  returned: always
  type: dict
  elements: str
  sample: {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Origin": "*",
    "Connection": "keep-alive",
    "Content-Length": "51",
    "Content-Type": "application/json",
    "Date": "Sat, 10 Jul 2021 23:14:14 GMT",
    "Server": "gunicorn/19.9.0"
  }
reason:
  description: response status reason
  returned: always
  type: str
  sample: "OK"
status_code:
  description: response status code
  returned: always
  type: str
  sample: 200
request:
  description: the original request, useful for debugging
  returned: when log_request == true
  type: complex
  contains:
    body:
      description: request body
      returned: always
      type: str
    headers:
      description: request headers. Authorization will be censored unless `log_auth` == true
      returned: always
      type: dict
      elements: str
    method:
      description: request HTTP method
      returned: always
      type: str
    path_url:
      description: request path url; the part of the url which is called the path; that's its technical name
      returned: always
      type: str
    url:
      description: the full url
      returned: always
      type: str
  sample: {
    "body": null,
    "headers": {
      "Accept": "*/*",
      "Accept-Encoding": "gzip, deflate",
      "Authorization": "Bearer hihello",
      "Connection": "keep-alive",
      "User-Agent": "python-requests/2.25.1"
    },
    "method": "GET",
    "path_url": "/bearer",
    "url": "https://httpbin.org/bearer"
  }
"""