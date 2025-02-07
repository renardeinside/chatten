import os
from pathlib import Path
from typing import Any
from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from chatten.dash_app import create_dash_app
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
from databricks.sdk.service.serving import ChatMessage
from databricks.sdk.service.serving import ChatMessageRole
import mimetypes
import json

from chatten.models import ApiChatMetadata, ApiChatResponse, ChatRequest, RelevantPageReq
from chatten.state import StatefulApp


app = FastAPI()

dotenv_file = Path(__file__).parent.parent.parent / ".env"

if dotenv_file.exists():
    logger.info(f"Loading environment variables from {dotenv_file}")
    load_dotenv(dotenv_file)
else:
    logger.info(f"Environment variables file not found: {dotenv_file}")


ENDPOINT_NAME = os.environ["SERVING_ENDPOINT"]


api_app = StatefulApp()

dash_app = create_dash_app()

# note: the order of mounting is important!
app.mount("/api", api_app)
app.mount("/", WSGIMiddleware(dash_app.server))


# only used for development, feel free to add if-else switch for production
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@api_app.post("/chat", response_model=ApiChatResponse)
async def chat_with_llm(request: ChatRequest, background_tasks: BackgroundTasks):

    logger.info(f"Received message: {request.message}, using endpoint: {ENDPOINT_NAME}")

    result = api_app.state.client.serving_endpoints.query(
        name=ENDPOINT_NAME,
        max_tokens=250,
        messages=[
            ChatMessage(
                content=request.message,
                role=ChatMessageRole.USER,
            )
        ],
    )
    try:
        # we expect the incoming response to be a single message with all content packed in it
        # The JSON will look like this:
        # [
        #   {"type": "ai_response", "content": "response content"},
        #   {"type": "tool_response", "responses": [
        #       {"metadata": {"file_name": "file.pdf", "year": 2021, "chunk_num": 0, "char_length": 1000}, "content": "retrieved text from file"},
        #   ]}
        # ]
        # the try-catch is implemented because sometimes bot can return an empty response without any content
        messages: list[dict[str, Any]] = json.loads(result.choices[0].message.content)

        content = [
            message.get("content")
            for message in messages
            if message.get("type") == "ai_response" and message.get("content")
        ][0]

        raw_metadata_responses = sum(
            [
                msg.get("responses")
                for msg in messages
                if msg.get("type") == "tool_response" and msg.get("responses")
            ],
            [],
        )

        metadata: list[ApiChatMetadata] = [
            ApiChatMetadata.model_validate(
                {**response.get("metadata"), "content": response.get("content")}
            )
            for response in raw_metadata_responses
            if response.get("metadata")
        ]
        for meta in metadata:
            if meta.file_name:
                # put files in background download and store in cache
                background_tasks.add_task(
                    api_app.state.file_cache.download_file, meta.file_name
                )

        return ApiChatResponse(content=content, metadata=metadata)
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        logger.error(f"Raw response: {result}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@api_app.get("/files")
def get_files(file_name: str):
    """Serve file by name (from cache, but will be downloaded if necessary)."""

    mime_type, _ = mimetypes.guess_type(file_name)
    mime_type = mime_type or "application/octet-stream"  # Default if unknown

    return StreamingResponse(
        api_app.state.file_cache.get_as_iterable(file_name),
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
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
