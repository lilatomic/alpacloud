from dataclasses import dataclass
from pathlib import Path

import click
import requests
from bs4 import BeautifulSoup


@dataclass
class AlpineRepo:
	version: str
	base_url: str = "https://git.alpinelinux.org/"

	def get(self, url) -> requests.Response:
		return requests.get(self.base_url + url, params={"h": self.version})

	def get_page(self, url):
		soup = BeautifulSoup(self.get(url).text, features="html.parser")
		return soup

	def listdir(self, dir) -> dict[str, str]:
		page = self.get_page(dir)

		rows = iter(page.find("table", {"summary": "tree listing"}).find_all("tr"))
		header = next(rows)  # escape header

		dir_items = {}
		for row in rows:
			link = row.find("a", class_="ls-blob")
			dir_items[link.text] = link.attrs["href"]

		return dir_items

	def get_file(self, file_link) -> bytes:
		plain_file_link = file_link.replace("aports/tree", "aports/plain")
		return self.get(plain_file_link).content

	def vendor_pkg(self, package) -> dict[str, bytes]:
		files = self.listdir("aports/tree/main/" + package)

		contents = {}
		for name, link in files.items():
			contents[name] = self.get_file(link)

		return contents


@click.command()
@click.option("--package")
@click.option("--version", help="version of alpine to pull from")
@click.option("--dst", help="the destination name to use for the vendored package")
def run(package, version, dst):
	base_path = Path(dst)

	r = AlpineRepo(version)
	files = r.vendor_pkg(package)

	base_path.mkdir(exist_ok=True, parents=True)
	for name, content in files.items():
		dst = base_path / name
		with open(dst, "wb") as f:
			f.write(content)


if __name__ == "__main__":
	run()
