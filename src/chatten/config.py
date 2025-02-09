from pathlib import Path, PosixPath
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = Path(__file__).parent.parent.parent / ".env"

if env_file.exists():
    logger.info(f"Using environment file: {env_file}")


class Config(BaseSettings):
    profile: str | None = None  # Databricks CLI profile, useful for local testing

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",  # for nested configuration
        env_prefix="CHATTEN_",  # for app-based configuration
        cli_parse_args=True,  # for command-line based configuration
    )

    catalog: str
    db: str = "chatten"
    volume: str = "main"

    # paths in the volume
    docs_path: PosixPath = PosixPath("raw_docs")

    # checkpoint locations in the volume
    raw_docs_checkpoint_location: PosixPath = PosixPath("checkpoints/raw")
    processed_docs_checkpoint_location: PosixPath = PosixPath("checkpoints/processed")

    # table names
    docs_table: str = "docs"

    # vector search index name
    vsi: str = "vsi"

    # agent serving endpoint
    agent_serving_endpoint: str = "chatten_agent"

    # chat endpoint
    chat_endpoint: str = "databricks-meta-llama-3-3-70b-instruct"

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
    def vsi_full_name(self):
        return f"{self.catalog}.{self.db}.{self.vsi}"

    @property
    def docs_full_name(self):
        return f"{self.catalog}.{self.db}.{self.docs_table}"
