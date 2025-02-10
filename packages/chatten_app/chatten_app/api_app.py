import mimetypes
from pathlib import PosixPath
from chatten_app.models import (
    ApiChatMetadata,
    ApiChatResponse,
    ChatRequest,
    ChatResponse,
    RelevantPageReq,
)
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from fastapi import BackgroundTasks, FastAPI

from chatten_app.state import AppState
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger


class StatefulApp(FastAPI):
    """FastAPI app with a state object that contains the client and file cache.
    Again, subclassing is used to add strong typing.

    Note that initialization happens only once, when the app is starting.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state: AppState = AppState()


api_app = StatefulApp()


@api_app.post("/chat", response_model=ApiChatResponse)
async def chat_with_llm(request: ChatRequest, background_tasks: BackgroundTasks):

    logger.info(
        f"Received message: {request.message}, using endpoint: {api_app.state.config.agent_serving_endpoint_name}"
    )

    result = api_app.state.client.serving_endpoints.query(
        name=api_app.state.config.agent_serving_endpoint_name,
        max_tokens=250,
        messages=[
            ChatMessage(
                content=request.message,
                role=ChatMessageRole.USER,
            )
        ],
    )
    try:
        # all content is in the first choice, packed in a JSON serialized string
        raw_content = result.choices[0].message.content
        response = ChatResponse.from_content(raw_content)

        for source in response.sources:
            background_tasks.add_task(
                api_app.state.file_cache.download_file, source.path
            )

        return ApiChatResponse(
            content=response.content,
            metadata=[
                ApiChatMetadata(content=source.query, file_name=source.path)
                for source in response.sources
            ],
        )

    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        logger.error(f"Raw response: {result}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@api_app.get("/files")
def get_files(file_name: PosixPath):
    """Serve file by name (from cache, but will be downloaded if necessary)."""

    mime_type, _ = mimetypes.guess_type(file_name.as_posix())
    mime_type = mime_type or "application/octet-stream"  # Default if unknown

    return StreamingResponse(
        api_app.state.file_cache.get_as_iterable(file_name),
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_name.as_posix()}"'
        },
    )


@api_app.post("/files/relevant_page")
def get_relevant_page(req: RelevantPageReq):
    """Get the most relevant page for a given query in a file."""
    with api_app.state.file_cache._lock:
        assert (
            req.file_name in api_app.state.file_cache._cache
        ), f"File {req.file_name} not in cache"
        content = api_app.state.file_cache._cache[req.file_name]
    page_num = content.find_best_match(req.query)
    return JSONResponse(content={"page_num": page_num})
