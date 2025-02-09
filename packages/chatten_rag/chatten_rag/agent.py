import json
from typing import Iterator
from databricks_langchain import ChatDatabricks
from mlflow.langchain.output_parsers import ChatCompletionOutputParser
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableGenerator
from loguru import logger
from langgraph.pregel.io import AddableValuesDict
from langchain_core.documents import Document

from databricks_langchain import VectorSearchRetrieverTool
from pydantic import BaseModel


class SerializedVectorSearchRetrieverTool(VectorSearchRetrieverTool):

    def _run(self, query: str) -> str:
        raw_result: list[Document] = super()._run(query)
        _serialized = [doc.model_dump() for doc in raw_result]
        return json.dumps(_serialized)


retriever_tool = SerializedVectorSearchRetrieverTool(
    index_name="ivt.chatten.vsi",
    num_results=3,
    tool_name="retriever",
    tool_description="Search through document corpus stored in Vector Search Index. Provides helpful insights about Databricks.",
)

llm = ChatDatabricks(model="databricks-meta-llama-3-3-70b-instruct")

prompt = """
You are a helpful assistant on all topics related to Databricks. 
Always return the result in a Markdown format.
Almost always try to use the retriever tool to search through the document corpus, 
    especially when the user asks a question.
"""

raw_agent = create_react_agent(
    llm,
    tools=[retriever_tool],
    prompt=prompt,
)


class SourceInfo(BaseModel):
    path: str


class StructuredOutput(BaseModel):
    content: str  # main response content
    sources: list[SourceInfo]  # sources used to generate the response


def wrap_output(stream: Iterator[AddableValuesDict]) -> Iterator[str]:

    for event in stream:
        messages: list[AIMessage | HumanMessage | ToolMessage] = event["messages"]
        _payload = {}

        last_tool_message = [
            message for message in messages if isinstance(message, ToolMessage)
        ][-1]
        last_ai_message = [
            message for message in messages if isinstance(message, AIMessage)
        ][-1]

        _payload["content"] = last_ai_message.content

        _docs = [Document(**doc) for doc in json.loads(last_tool_message.content)]
        _payload["sources"] = [
            SourceInfo(path=doc.metadata.get("path")) for doc in _docs
        ]

        _output = StructuredOutput(**_payload)
        yield _output.model_dump_json(indent=2)


agent = raw_agent | RunnableGenerator(wrap_output) | ChatCompletionOutputParser()

_response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is unity catalog?"}]}
)
