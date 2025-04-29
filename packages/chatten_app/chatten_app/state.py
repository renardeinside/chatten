from cachetools import TTLCache
from chatten_app.models import ApiChatResponse, ChatRequest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.files import DownloadResponse
from pypdf import PdfReader
from pathlib import PosixPath
from threading import Lock
from typing import Generator
import rapidfuzz
from loguru import logger
from pydantic import BaseModel
import time
import functools

from io import BytesIO

from starlette.datastructures import State

from chatten.config import Config


class FileContent(BaseModel):
    """Model to store file content in cache.

    Raw represents the raw bytes of the file.
    Extracted_pages is a list of strings where each string represents the text extracted from a page of the file.
    """

    raw: bytes
    extracted_pages: list[str]

    @property
    def as_io(self) -> BytesIO:
        """Returns the raw bytes as a BytesIO object. Useful for streaming."""
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
            return 1  # page number starts from 1, return 1 if no relevant page found

        logger.info(f"Found relevant page for query: {_query} at index: {index}")
        return index + 1  # page number starts from 1


class FileCache:
    """Cache for storing file contents.

    The cache is a TTLCache with a maximum size and a time-to-live (TTL) for each entry.
    Cache is thread-safe, and it uses a lock to prevent threading issues.
    """

    def __init__(
        self,
        client: WorkspaceClient,
        volume_path: PosixPath,
        max_size: int = 100,
        ttl_in_seconds: int = 3600,
    ):
        self._cache: TTLCache[PosixPath, FileContent] = TTLCache(
            maxsize=max_size, ttl=ttl_in_seconds
        )  # Auto eviction after TTL
        self._client = client
        self._volume_path = volume_path

        # we need lock to prevent threading issues
        self._lock = Lock()

    def download_file(self, path: PosixPath) -> None:
        """
        Path should be just the file name, not the full path.
        """
        with self._lock:
            if path not in self._cache:
                full_path = self._volume_path / path
                logger.info(f"Downloading file: {full_path} from Volume into cache")
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
        self, path: PosixPath, chunk_size: int = 10 * 1024 * 1024
    ) -> Generator[bytes, None, None]:
        """Returns an iterator with file chunks."""

        # retry 2-3 times if file not in cache, usually happens while file is being downloaded
        found = False
        for _ in range(3):
            time.sleep(0.5)
            with self._lock:
                if path in self._cache:
                    found = True
                    break

        # if file not found in cache after retries, download it
        if not found:
            self.download_file(path)

        with self._lock:
            content = self._cache[path]

        return iter(functools.partial(content.as_io.read, chunk_size), b"")

class ResponsesCache:
    def __init__(self):
        self._responses: TTLCache[ChatRequest, ApiChatResponse] = TTLCache(maxsize=100, ttl=60*2)  # 2 minutes
        self._lock = Lock()

    def __contains__(self, request: ChatRequest) -> bool:
        with self._lock:
            result = request in self._responses
            logger.info(f"Checking if request {request} is in cache, actual {result}")
            return result

    def get(self, request: ChatRequest) -> ApiChatResponse:
        with self._lock:
            return self._responses.get(request, None)

    def set(self, request: ChatRequest, response: ApiChatResponse) -> None:
        with self._lock:
            self._responses[request] = response

class AppState(State):
    """State class for storing the client and file cache.
    We're using subclassing to add strong typing.
    """

    def __init__(self, state=None):
        super().__init__(state)
        self.config = Config()
        logger.info(f"Config: {self.config.model_dump_json(indent=4)}")
        self.client = WorkspaceClient(profile=self.config.profile)
        self.file_cache = FileCache(self.client, self.config.full_raw_docs_path)
        self.responses_cache = ResponsesCache()
