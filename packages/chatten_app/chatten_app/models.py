from __future__ import annotations
from pathlib import PosixPath
from pydantic import BaseModel, Field, field_validator
from pydantic_core import from_json
from typing import Literal, Annotated, Any



class ChatRequest(BaseModel):
    message: str


class ApiChatMetadata(BaseModel):
    content: str
    file_name: PosixPath
    year: int | None = None


class ApiChatResponse(BaseModel):
    content: str
    metadata: list[ApiChatMetadata]
    error_happened: bool = False


class RelevantPageReq(BaseModel):
    file_name: PosixPath
    query: str


class HumanMessage(BaseModel):
    message_type: Literal["human"] = Field(alias="type")
    content: str


class AiMessage(BaseModel):
    message_type: Literal["ai"] = Field(alias="type")
    content: str


class SourceInfo(BaseModel):
    query: str
    path: PosixPath

    @field_validator("path", mode="before")
    @classmethod
    def val_path(cls, value: Any) -> PosixPath:
        assert isinstance(value, str), "path must be a string"
        return PosixPath(value.split("/")[-1])  # only the file name is needed


class ToolMessage(BaseModel):
    message_type: Literal["tool"] = Field(alias="type")
    metadata: list[SourceInfo] = Field(alias="content")

    @field_validator("metadata", mode="before")
    @classmethod
    def val_content(cls, value: Any) -> list[SourceInfo]:
        assert isinstance(value, str), "content must be a string"
        raw_info = from_json(value)
        return [
            SourceInfo(query=raw["page_content"], path=raw["metadata"]["path"])
            for raw in raw_info
        ]


Message = Annotated[
    ToolMessage | HumanMessage | AiMessage, Field(discriminator="message_type")
]


class ChatResponse(BaseModel):
    messages: list[Message]

    @classmethod
    def from_content(cls, raw_content: str) -> ChatResponse:
        return cls(messages=from_json(raw_content))

    @property
    def content(self) -> str:
        ai_message = next(
            message for message in self.messages if message.message_type == "ai" and message.content
        )
        return ai_message.content

    @property
    def sources(self) -> list[SourceInfo]:
        tool_message = next(
            message for message in self.messages if message.message_type == "tool"
        )
        return tool_message.metadata
