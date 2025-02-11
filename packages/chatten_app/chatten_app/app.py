import asyncio
from contextlib import asynccontextmanager
from pathlib import PosixPath
from fastapi import FastAPI
from chatten_app.dash_app import create_dash_app
from fastapi.middleware.wsgi import WSGIMiddleware
from loguru import logger
from chatten_app.api_app import api_app
import concurrent.futures


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload the big files on app startup to avoid latency during the first request."""
    logger.info("Starting the app and preloading files")
    files = {
        PosixPath(file.name): file.file_size
        for file in api_app.state.client.files.list_directory_contents(
            api_app.state.config.full_raw_docs_path.as_posix()
        )
        if not file.is_directory
    }
    top_files_by_size: list[PosixPath] = sorted(files, key=files.get, reverse=True)[
        : api_app.state.config.max_files_to_preload
    ]

    async def download_files():
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                loop.run_in_executor(
                    executor, api_app.state.file_cache.download_file, file
                )
                for file in top_files_by_size
            ]
            for future in asyncio.as_completed(futures):
                try:
                    await future
                except Exception as exc:
                    logger.warning(f"Startup-time file download failed with: {exc}")

    asyncio.create_task(download_files())

    yield

    logger.info("Stopping the app")


app = FastAPI(lifespan=lifespan)

dash_app = create_dash_app()

# note: the order of mounting is important!
app.mount("/api", api_app)
app.mount("/", WSGIMiddleware(dash_app.server))
