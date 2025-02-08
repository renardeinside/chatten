import collections
from functools import partial
from pathlib import PosixPath
import requests
from chatten.config import Config
from chatten_rag.common import Task
from concurrent.futures import ThreadPoolExecutor


class Loader(Task[Config]):
    config_class = Config

    def _download_file(self, url: str, destination: PosixPath) -> PosixPath:
        filename = PosixPath(url.split("/")[-1])
        local_filename = destination / filename

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            self.logger.info(f"Downloading {url} to {local_filename}")
            with local_filename.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    # if chunk:
                    f.write(chunk)
        return local_filename

    def download_file_from_git(self, dest: PosixPath, owner, repo, path):

        if not dest.exists():
            dest.mkdir(parents=True)

        files = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents{path}"
        ).json()
        files = [f["download_url"] for f in files if "NOTICE" not in f["name"]]
        files = [
            f.replace(
                "https://raw.githubusercontent.com/databricks-demos/dbdemos-dataset/main/",
                "https://dbdemos-dataset.s3.amazonaws.com/",
            )
            for f in files
        ]

        downloader = partial(self._download_file, destination=dest)

        with ThreadPoolExecutor(max_workers=10) as executor:
            collections.deque(executor.map(downloader, files))

    def run(self):
        self.logger.info("Downloading files from git")
        self.download_file_from_git(
            self.config.volume_path,
            "databricks-demos",
            "dbdemos-dataset",
            "/llm/databricks-pdf-documentation",
        )
