from pathlib import Path, PosixPath
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = Path(__file__).parent.parent.parent / ".env"

if env_file.exists():
    logger.info(
        f"Using environment file: {env_file}"
    )  # pydantic-settings will automatically load the environment variables from the .env file


class Config(BaseSettings):
    profile: str | None = None  # Databricks CLI profile, useful for local testing

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # for nested configuration
        env_prefix="CHATTEN_",  # for app-based configuration
        cli_parse_args=True,  # for command-line based configuration
        cli_ignore_unknown_args=True,  # ignore unknown command-line arguments
    )

    catalog: str
    db: str = "chatten"
    volume: str = "main"

    PROMPT: str = """
    You are a helpful assistant on all topics related to Databricks. 
    Always return the result in a Markdown format.
    Almost always try to use the retriever tool to search through the document corpus, 
        especially when the user asks a question.
    """

    # paths in the volume
    docs_path: PosixPath = PosixPath("raw_docs")

    # checkpoint locations in the volume
    raw_docs_checkpoint_location: PosixPath = PosixPath("checkpoints/raw")

    # table names
    docs_table: str = "docs"

    # vector search index name
    vsi: str = "vsi"

    # agent serving endpoint
    agent_serving_endpoint: str = "chatten_agent"

    # chat endpoint, to be used in the agent
    chat_endpoint: str = "databricks-meta-llama-3-3-70b-instruct"

    # amout of files preloaded in the file cache when app starts
    max_files_to_preload: int = 10

    @property
    def volume_path(self) -> PosixPath:
        # note the /Volumes prefix, leading slash is important!
        return PosixPath("/Volumes") / self.catalog / self.db / self.volume

    @property
    def full_raw_docs_path(self) -> PosixPath:
        return self.volume_path / self.docs_path

    @property
    def full_raw_docs_checkpoint_location(self) -> str:
        return (
            "dbfs:" + (self.volume_path / self.raw_docs_checkpoint_location).as_posix()
        )

    @property
    def vsi_with_catalog(self):
        return f"{self.catalog}.{self.db}.{self.vsi}"

    @property
    def docs_with_catalog(self):
        return f"{self.catalog}.{self.db}.{self.docs_table}"

    @property
    def agent_serving_endpoint_with_catalog(self):
        return f"{self.catalog}.{self.db}.{self.agent_serving_endpoint}"

    @property
    def as_model_config(self):
        # used to serialize the model_config into a tempfile for mlflow
        return {
            "chat_endpoint": self.chat_endpoint,
            "vsi": self.vsi_with_catalog,
            "PROMPT": self.PROMPT,
        }

    @property
    def agent_serving_endpoint_name(self):
        # when databricks.agents.deploy is called, it will deploy the model to this endpoint
        return f"agents_{self.catalog}-{self.db}-{self.agent_serving_endpoint}"
