"""Vendor all the files of an Alpine package"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import click
import requests
from bs4 import BeautifulSoup


@dataclass
class AlpineRepo:
	"""Descriptor for an Alpine repository."""

	version: str
	base_url: str = "https://git.alpinelinux.org/"

	def get(self, url) -> requests.Response:
		"""Make a request to the Alpine respository website"""
		return requests.get(self.base_url + url, params={"h": self.version})

	def get_page(self, url: str) -> BeautifulSoup:
		"""Read an Alpine package's page"""
		soup = BeautifulSoup(self.get(url).text, features="html.parser")
		return soup

	def listdir(self, dir) -> dict[str, str]:
		"""List files in a directory in an alpine repo"""
		page = self.get_page(dir)

		rows = iter(page.find("table", {"summary": "tree listing"}).find_all("tr"))  # type: ignore
		next(rows)  # escape header

		dir_items = {}
		for row in rows:
			link = row.find("a", class_="ls-blob")
			dir_items[link.text] = link.attrs["href"]

		return dir_items

	def get_file(self, file_link) -> bytes:
		"""Get a single file from the alpine repo"""
		plain_file_link = file_link.replace("aports/tree", "aports/plain")
		return self.get(plain_file_link).content

	def vendor_pkg(self, package) -> dict[str, bytes]:
		"""Fetch all files from the alpine repo"""
		files = self.listdir("aports/tree/main/" + package)

		contents = {}
		for name, link in files.items():
			contents[name] = self.get_file(link)

		return contents


def apply_git_patches(patch_dir: Path, dst: Path):
	"""Applies all git patch files in the specified directory."""
	patches = [f for f in os.listdir(patch_dir) if f.endswith(".patch")]
	patches.sort()

	for patch in patches:
		patch_path = os.path.join(patch_dir, patch)
		try:
			print(f"Applying patch {patch}...")
			argv = ["git", "apply", str(patch_path), "--include", str(dst / "*")]
			result = subprocess.run(argv, check=True, text=True, capture_output=True)
			print(result.stdout)
		except subprocess.CalledProcessError as e:
			raise RuntimeError(f"Failed to apply patch {patch}") from e


@click.command()
@click.option("--package")
@click.option("--version", help="version of alpine to pull from")
@click.option("--dst", help="the destination name to use for the vendored package")
def run(package, version, dst):
	"""Vendor an Alpine package's files"""
	base_path = Path(dst)

	r = AlpineRepo(version)
	files = r.vendor_pkg(package)

	base_path.mkdir(exist_ok=True, parents=True)
	for name, content in files.items():
		dst_file = base_path / name
		with open(dst_file, "wb") as f:
			f.write(content)

	apply_git_patches(Path("dev/alpine/metapatches"), base_path)


if __name__ == "__main__":
	run()  # pylint: disable=no-value-for-parameter
