from pathlib import Path, PosixPath
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = Path(__file__).parent.parent.parent / ".env"

if env_file.exists():
    logger.info(f"Using environment file: {env_file}")

class Config(BaseSettings):
    volume_path: PosixPath
    serving_endpoint: str

    model_config = SettingsConfigDict(
        env_prefix="CHATTEN_",  # for app-based configuration
        cli_parse_args=True # for command-line based configuration
    )