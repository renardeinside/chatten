import os
from pathlib import Path
from typing import Annotated, Any, BinaryIO, Generator
from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from chatten.dash_app import create_dash_app
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage
from databricks.sdk.service.serving import ChatMessageRole
from databricks.sdk.service.files import DownloadResponse
from databricks.sdk._base_client import _StreamingResponse
from databricks.sdk.errors.platform import NotFound
import mimetypes

import json

app = FastAPI()
api_app = FastAPI()

dotenv_file = Path(__file__).parent.parent.parent / ".env"

if dotenv_file.exists():
    logger.info(f"Loading environment variables from {dotenv_file}")
    load_dotenv(dotenv_file)
else:
    logger.info(f"Environment variables file not found: {dotenv_file}")


ENDPOINT_NAME = os.environ["SERVING_ENDPOINT"]
VOLUME_PATH = os.environ["VOLUME_PATH"]

# dash_app = create_dash_app()
# app.mount("/", WSGIMiddleware(dash_app.server))
app.mount("/api", api_app)


class ChatRequest(BaseModel):
    message: str


api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def client() -> WorkspaceClient:
    return WorkspaceClient()  # App SPN


class ApiChatMetadata(BaseModel):
    file_name: str
    year: int | None
    chunk_num: int
    char_length: int


class ApiChatResponse(BaseModel):
    content: str
    metadata: list[ApiChatMetadata]
    error_happened: bool = False


@api_app.post("/chat", response_model=ApiChatResponse)
async def chat_with_llm(
    request: ChatRequest, client: Annotated[WorkspaceClient, Depends(client)]
):

    logger.info(f"Received message: {request.message}, using endpoint: {ENDPOINT_NAME}")

    result = client.serving_endpoints.query(
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
            ApiChatMetadata.model_validate(response.get("metadata"))
            for response in raw_metadata_responses
            if response.get("metadata")
        ]

        return ApiChatResponse(content=content, metadata=metadata)
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        logger.error(f"Raw response: {result}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@api_app.get("/files")
def get_files(file_name: str, client: Annotated[WorkspaceClient, Depends(client)]):
    full_path = f"{VOLUME_PATH}/{file_name}"

    logger.info(f"Downloading file: {full_path}")

    try:
        metadata = client.files.get_metadata(full_path)
    except NotFound:
        return JSONResponse(status_code=404, content={"error": "File not found"})

    logger.info(f"File metadata: {metadata}")

    response: DownloadResponse = client.files.download(full_path)
    io: BinaryIO = response.contents

    mime_type, _ = mimetypes.guess_type(file_name)
    mime_type = mime_type or "application/octet-stream"  # Default if unknown

    def iter_file():
        for chunk in iter(lambda: io.read(1024 * 64), b""):  # Read in 64KB chunks
            yield chunk

    return StreamingResponse(
        iter_file(),
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
