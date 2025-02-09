import json
from typing import Iterator
from databricks_langchain import ChatDatabricks
from mlflow.langchain.output_parsers import ChatCompletionOutputParser
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableGenerator
from langgraph.pregel.io import AddableValuesDict
from langchain_core.documents import Document

from databricks_langchain import VectorSearchRetrieverTool
from chatten.config import Config
from chatten.models import StructuredOutput, SourceInfo


class SerializedVectorSearchRetrieverTool(VectorSearchRetrieverTool):

    def _run(self, query: str) -> str:
        raw_result: list[Document] = super()._run(query)
        _serialized = [doc.model_dump() for doc in raw_result]
        return json.dumps(_serialized)


def get_agent(config: Config):
    retriever_tool = SerializedVectorSearchRetrieverTool(
        index_name=config.vsi_full_name,
        num_results=3,
        tool_name="retriever",
        tool_description="Search through document corpus stored in Vector Search Index. Provides helpful insights about Databricks.",
    )

    llm = ChatDatabricks(model=config.chat_endpoint)

    raw_agent = create_react_agent(
        llm,
        tools=[retriever_tool],
        prompt=config.PROMPT,
    )

    def wrap_output(stream: Iterator[AddableValuesDict]) -> Iterator[str]:

        for event in stream:
            messages = event["messages"]
            last_tool_message = next(
                msg for msg in reversed(messages) if isinstance(msg, ToolMessage)
            )
            last_ai_message = next(
                msg for msg in reversed(messages) if isinstance(msg, AIMessage)
            )

            docs = [Document(**doc) for doc in json.loads(last_tool_message.content)]
            sources = [
                SourceInfo(content=doc.page_content, path=doc.metadata.get("path"))
                for doc in docs
            ]

            yield StructuredOutput(
                content=last_ai_message.content, sources=sources
            ).model_dump_json(indent=2)

    agent = raw_agent | RunnableGenerator(wrap_output) | ChatCompletionOutputParser()
    return agent
