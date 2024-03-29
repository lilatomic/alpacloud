"""Execute HTTP requests in Ansible"""
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase

try:
	import requests
	from requests import Response
	from requests.auth import AuthBase, HTTPBasicAuth

	import_error = None
except ImportError as import_guard:
	import_error = import_guard

NS = "lilatomic_api_http"
AUTHORIZATION_HEADER = "Authorization"
DEFAULT_TIMEOUT = 15


class HTTPBearerAuth(AuthBase):
	"""HTTP Bearer authentication"""

	def __init__(self, token, header=AUTHORIZATION_HEADER, value_format="Bearer {}"):
		self.token = token
		self.header = header
		self.value_format = value_format

	def __call__(self, r):
		r.headers[self.header] = self.value_format.format(self.token)
		return r


class ConnectionInfo:
	"""Information for an HTTP connection"""

	def __init__(self, base, auth=None, kwargs=None):
		self.base = base
		self.auth = self.make_auth(auth)
		self.kwargs = kwargs or {}

	@staticmethod
	def make_auth(params) -> Optional[AuthBase]:
		"""Build authentication header"""
		if params is None or params == {}:
			return None
		auth_method = params.pop("method", "basic")
		if auth_method == "basic":
			return HTTPBasicAuth(params["username"], params["password"])
		elif auth_method == "bearer":
			return HTTPBearerAuth(**params)
		else:
			return None


def resolve_connection_info(task_vars, info: Union[Dict, str]):
	"""Get the connection info from globals or supplied information"""
	if isinstance(info, str):  # info is a connection name
		d = task_vars[NS][info]
	else:  # info is connection properties
		d = info
	return ConnectionInfo(**d)


class ActionModule(ActionBase):
	"""Execute HTTP requests in Ansible"""

	def run(self, tmp=None, task_vars=None):
		"""Run Ansible module"""
		super().run(tmp=tmp, task_vars=task_vars)

		if import_error:
			raise AnsibleError("Install dependencies") from import_error

		connection_info = resolve_connection_info(task_vars, self.arg("connection"))
		task_kwargs = self.arg_or("kwargs", {})

		method = self.arg_or("method", "GET")
		data = self.arg_or("data")
		json = self.arg_or("json")

		headers = self.arg_or("headers")

		request_kwargs = recursive_merge(
			recursive_merge(connection_info.kwargs, task_kwargs), {"headers": headers}
		)

		request_kwargs["timeout"] = self.arg_or(
			"timeout", request_kwargs.get("timeout", DEFAULT_TIMEOUT)
		)

		r = requests.request(
			method,
			urljoin(connection_info.base + "/", self.arg("path").strip("/")),
			auth=connection_info.auth,
			data=data,
			json=json,
			**request_kwargs
		)

		out = {}

		# response status
		out["failed"] = not self.is_ok(r, self.arg_or("status_code"))

		# response data
		if r.headers.get("Content-Type", None) == "application/json":
			out["json"] = r.json()
		out["msg"] = r.text

		# parameters for ansible.legacy.uri module
		out.update(
			{
				"content": r.content,
				"content_length": r.headers.get("Content-Length", None),
				"content_type": r.headers.get("Content-Type", None),
				"cookies": dict(r.cookies),
				"date": r.headers.get("Date", None),
				"elapsed": r.elapsed.seconds,
				"redirected": r.is_redirect,
				"server": r.headers.get("Server", None),
				"status": r.status_code,
				"url": r.url,
			}
		)

		# other parameters
		out.update(
			{
				"encoding": r.encoding,
				"headers": r.headers,
				"reason": r.reason,
				"status_code": r.status_code,
			}
		)

		# request parameters, for debugging
		if self.arg_or("log_request"):
			req = r.request
			headers = req.headers.copy()
			if not self.arg_or("log_auth"):
				if AUTHORIZATION_HEADER in headers:
					headers[AUTHORIZATION_HEADER] = "*" * len(
						headers[AUTHORIZATION_HEADER]
					)

			out.update(
				{
					"request": {
						"body": req.body,
						"headers": headers,
						"method": req.method,
						"path_url": req.path_url,
						"url": req.url,
					}
				}
			)

		return out

	@staticmethod
	def is_ok(response: Response, acceptable_codes: Optional[List[int]] = None):
		"""Validate if response-code is within the acceptable ones"""
		if acceptable_codes:
			return response.status_code in acceptable_codes
		else:
			return response.ok

	@staticmethod
	def parse_content_length(content_length: Optional[str]) -> Optional[int]:
		"""Try parsing content-length"""
		if content_length:
			try:
				return int(content_length)
			except ValueError:
				return None
		return None

	def arg(self, arg):
		"""Get task argument, failing if not found"""
		return self._task.args[arg]

	def arg_or(self, arg, default=None):
		"""Get task argument with default"""
		return self._task.args.get(arg, default)


def recursive_merge(a: Dict, b: Dict, path=None) -> Dict:
	"""Recursively merges dictionaries
	Mostly taken from user `andrew cooke` on [stackoverflow](https://stackoverflow.com/a/7205107)
	"""
	path = path or []
	out = a.copy()
	for k in b:
		if k in a:
			if isinstance(a[k], dict) and isinstance(b[k], dict):
				out[k] = recursive_merge(a[k], b[k], path + [str(k)])
			else:
				out[k] = b[k]
		else:
			out[k] = b[k]
	return out
