from pydantic import BaseModel


class SourceInfo(BaseModel):
    path: str
    content: str


class StructuredOutput(BaseModel):
    content: str  # main response content
    sources: list[SourceInfo]  # sources used to generate the response
