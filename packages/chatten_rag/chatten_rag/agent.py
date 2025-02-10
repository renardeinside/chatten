import json
from typing import Iterator
from databricks_langchain import ChatDatabricks
from mlflow.langchain.output_parsers import ChatCompletionOutputParser
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableGenerator
from langgraph.pregel.io import AddableValuesDict
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage

from databricks_langchain import VectorSearchRetrieverTool
from mlflow.models import ModelConfig
import mlflow


class SerializedVectorSearchRetrieverTool(VectorSearchRetrieverTool):

    def _run(self, query: str) -> str:
        raw_result: list[Document] = super()._run(query)
        _serialized = [doc.model_dump() for doc in raw_result]
        return json.dumps(_serialized)


def get_agent(chat_model: str, vsi: str, prompt: str):
    retriever_tool = SerializedVectorSearchRetrieverTool(
        index_name=vsi,
        num_results=3,
        tool_name="retriever",
        tool_description="Search through document corpus stored in Vector Search Index. Provides helpful insights about Databricks.",
        columns=["path"],
    )

    llm = ChatDatabricks(endpoint=chat_model)

    raw_agent = create_react_agent(
        llm,
        tools=[retriever_tool],
        prompt=prompt,
    )

    def wrap_output(stream: Iterator[AddableValuesDict]) -> Iterator[str]:

        for event in stream:

            if "agent" in event:
                messages: list[BaseMessage] = event["agent"]["messages"]

            elif "messages" in event:
                messages: list[BaseMessage] = event["messages"]

            packed_messages = [message.model_dump() for message in messages]
            yield json.dumps(packed_messages)

    _agent = raw_agent | RunnableGenerator(wrap_output) | ChatCompletionOutputParser()
    return _agent


config = ModelConfig(development_config="config.yml")

agent = get_agent(
    config.get("chat_endpoint"),
    config.get("vsi"),
    config.get("PROMPT"),
)

mlflow.models.set_model(agent)
