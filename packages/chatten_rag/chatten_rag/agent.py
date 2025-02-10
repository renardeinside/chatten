import json
from typing import Iterator
from databricks_langchain import ChatDatabricks
from mlflow.langchain.output_parsers import ChatCompletionOutputParser
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import RunnableLambda
from langgraph.pregel.io import AddableValuesDict
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage

from databricks_langchain import VectorSearchRetrieverTool


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

    llm = ChatDatabricks(model=chat_model)

    raw_agent = create_react_agent(
        llm,
        tools=[retriever_tool],
        prompt=prompt,
    )

    def wrap_output(state: AddableValuesDict) -> str:
        messages: list[BaseMessage] = state["messages"]
        packed_messages = [message.model_dump() for message in messages]
        return json.dumps(packed_messages)

    agent = raw_agent | RunnableLambda(wrap_output) | ChatCompletionOutputParser()
    return agent
