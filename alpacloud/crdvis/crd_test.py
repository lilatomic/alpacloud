import os
import shutil
import unittest
from unittest.mock import patch

import pytest

from alpacloud.crdvis.crd import CRDReadError, read_path
from alpacloud.crdvis.models import CustomResourceDefinition


class TestReadPath(unittest.TestCase):
	"""Integration tests for the read_path function."""

	def test_read_path_from_file(self):
		"""Test reading a CRD from a file."""
		# Get the path to the test file
		test_file_path = os.path.join("alpacloud/crdvis/test_resources/podmonitor.yaml")

		# Test with file:// prefix
		crd = read_path(f"file://{test_file_path}")
		self.assertIsInstance(crd, CustomResourceDefinition)
		self.assertEqual(crd.kind, "CustomResourceDefinition")

		# Test with direct path
		crd = read_path(test_file_path)
		self.assertIsInstance(crd, CustomResourceDefinition)
		self.assertEqual(crd.kind, "CustomResourceDefinition")

	def test_read_path_from_file_not_found(self):
		"""Test reading a CRD from a non-existent file."""
		with self.assertRaises(CRDReadError) as context:
			read_path("file:///nonexistent/file.yaml")
		self.assertIn("File not found", str(context.exception))

	def test_read_path_from_https(self):
		"""Test reading a CRD from a HTTPS URL."""
		url = "https://github.com/prometheus-operator/prometheus-operator/blob/main/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml"

		crd = read_path(url)
		self.assertIsInstance(crd, CustomResourceDefinition)
		self.assertEqual(crd.kind, "CustomResourceDefinition")

	def test_read_path_from_https_invalid_url(self):
		"""Test reading a CRD from an invalid HTTPS URL."""
		with self.assertRaises(CRDReadError) as context:
			read_path("https://example.com/nonexistent.yaml")
		self.assertIn("Failed to fetch CRD", str(context.exception))

	@pytest.mark.skipif(shutil.which("kubectl") is None, reason="kubectl is not installed")
	def test_read_path_from_kubectl(self):
		"""Test reading a CRD using kubectl."""
		crd = read_path("kubectl://podmonitors.monitoring.coreos.com")
		self.assertIsInstance(crd, CustomResourceDefinition)
		self.assertEqual(crd.kind, "CustomResourceDefinition")

	def test_read_path_from_kubectl_not_installed(self):
		"""Test reading a CRD using kubectl when kubectl is not installed."""
		# Mock shutil.which to return None, simulating kubectl not being installed
		with patch("shutil.which", return_value=None):
			with self.assertRaises(CRDReadError) as context:
				read_path("kubectl://podmonitors.monitoring.coreos.com")
			self.assertIn("kubectl is not installed", str(context.exception))

	def test_read_path_empty_content(self):
		"""Test reading a CRD with empty content."""
		with self.assertRaises(CRDReadError) as context:
			read_path("")
		self.assertIn("Empty content", str(context.exception))


if __name__ == "__main__":
	unittest.main()
