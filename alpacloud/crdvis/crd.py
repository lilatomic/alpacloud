from __future__ import annotations

import os
import shutil
import subprocess
from urllib.parse import urlparse

import requests
import yaml
from pydantic import ValidationError

from alpacloud.crdvis.models import CustomResourceDefinition


class CRDReadError(Exception):
	"""Exception raised when there is an error reading a CRD."""

	pass


def read_path(path: str) -> CustomResourceDefinition:
	"""
	Read a path-like object to fetch a CRD.

	Raises:
		CRDReadError: If there is an error reading the CRD.
	"""
	if path.startswith("http://") or path.startswith("https://"):
		req = requests.Request("GET", path)

		url = urlparse(req.url)
		if url.netloc == "github.com":
			req.params["raw"] = "true"

		response = requests.Session().send(req.prepare(), timeout=30)

		if not response.ok:
			raise CRDReadError(f"Failed to fetch CRD from {path}: {response.status_code}")
		content = response.text
	elif path.startswith("file://") or os.path.exists(path):
		disk_path = path.rsplit("://", 1)[-1]
		if not os.path.exists(disk_path):
			raise CRDReadError(f"File not found: {disk_path}")

		with open(disk_path, "r", encoding="utf-8") as f:
			content = f.read()

	elif path.startswith("kubectl://"):
		kubectl_crd = path.rsplit("://", 1)[-1]
		kubectl_exe = shutil.which("kubectl")
		if not kubectl_exe:
			raise CRDReadError("kubectl is not installed.")

		try:
			content = subprocess.check_output([kubectl_exe, "get", "-o", "yaml", "crd", kubectl_crd], timeout=30).decode("utf-8")
		except subprocess.SubprocessError as e:
			try:
				crds = subprocess.check_output([kubectl_exe, "get", "crd"], timeout=30)
				if crds:
					error_msg = f"crd is not available in cluster {kubectl_crd}"
				else:
					error_msg = f"Failed to fetch CRDs {kubectl_crd}: {e}"

			except subprocess.SubprocessError as e:
				error_msg = f"Failed to fetch CRDs {kubectl_crd}: {e}"
			raise CRDReadError(error_msg)
	elif "://" in path:
		raise CRDReadError(f"Unsupported URL scheme: {path}")
	else:
		content = path

	if not content:
		raise CRDReadError("Empty content")

	try:
		doc = yaml.safe_load(content)
	except yaml.YAMLError as e:
		raise CRDReadError(f"CRD could not be loaded as YAML: {e}")

	try:
		return CustomResourceDefinition.model_validate(doc)
	except ValidationError as e:
		if isinstance(doc, str) and doc.count(".") >= 3:
			raise CRDReadError(f"CRD content looks like a name, did you mean `kubectl://{content}`")
		# escaping pydantic help message
		# like "Input should be a valid dictionary or instance of CustomResourceDefinition [type=model_type, input_value='applications.argoproj.io', input_type=str]"
		# for rich
		msg = str(e).replace("[", r"\[")
		raise CRDReadError(f"CRD could not be validated: {msg}")
