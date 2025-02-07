from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ApiChatMetadata(BaseModel):
    file_name: str
    year: int | None
    chunk_num: int
    char_length: int
    content: str


class ApiChatResponse(BaseModel):
    content: str
    metadata: list[ApiChatMetadata]
    error_happened: bool = False


class RelevantPageReq(BaseModel):
    file_name: str
    query: str