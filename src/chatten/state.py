from cachetools import TTLCache
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.files import DownloadResponse
from fastapi import FastAPI
from pypdf import PdfReader
from pathlib import PurePath
from threading import Lock
from typing import Generator
import rapidfuzz
from loguru import logger
from pydantic import BaseModel
import os
import time
import functools

from io import BytesIO

from starlette.datastructures import State


class FileContent(BaseModel):
    raw: bytes
    extracted_pages: list[str]

    @property
    def as_io(self) -> BytesIO:
        return BytesIO(self.raw)

    def find_best_match(self, query: str) -> int:
        # strip query to first 100 characters
        _query = query[:100].strip()
        best_page = max(
            self.extracted_pages,
            key=lambda page: rapidfuzz.fuzz.partial_ratio(page, _query),
            default="",
        )
        index = self.extracted_pages.index(best_page)

        if index <= 0:
            logger.warning(f"No relevant pages found for query: {_query}")
            return 1  # page number starts from 1

        logger.info(f"Found relevant page for query: {_query} at index: {index}")
        return index + 1  # page number starts from 1


class FileCache:
    def __init__(
        self, client: WorkspaceClient, max_size: int = 100, ttl_in_seconds: int = 3600
    ):
        self._cache: TTLCache[str, FileContent] = TTLCache(
            maxsize=max_size, ttl=ttl_in_seconds
        )  # Auto eviction after TTL
        self._client = client
        self._volume_path = PurePath(os.environ["VOLUME_PATH"])

        # we need lock to prevent threading issues
        self._lock = Lock()

    def download_file(self, path: str) -> None:
        with self._lock:
            if path not in self._cache:
                full_path = self._volume_path / path
                logger.info(f"Downloading file: {full_path}")
                response: DownloadResponse = self._client.files.download(
                    full_path.as_posix()
                )
                raw = response.contents.read()
                reader = PdfReader(BytesIO(raw))
                extracted_pages = [page.extract_text() for page in reader.pages]
                self._cache[path] = FileContent(
                    raw=raw, extracted_pages=extracted_pages
                )
                logger.info(f"Downloaded file: {full_path}")
            else:
                logger.info(f"File {path} already in cache, skipping download")

    def get_as_iterable(
        self, path: str, chunk_size: int = 65536
    ) -> Generator[bytes, None, None]:
        """Returns an iterator with file chunks of size 64KB."""
        # retry 2-3 times if file not in cache

        found = False
        for _ in range(3):
            time.sleep(0.5)
            with self._lock:
                if path in self._cache:
                    found = True
                    break

        assert found, f"File {path} not in cache"

        with self._lock:
            content = self._cache[path]

        return iter(functools.partial(content.as_io.read, chunk_size), b"")


class RichState(State):

    def __init__(self, state=None):
        super().__init__(state)
        logger.info("Creating state")
        self.client = WorkspaceClient()
        self.file_cache = FileCache(self.client)


class StatefulApp(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state: RichState = RichState()