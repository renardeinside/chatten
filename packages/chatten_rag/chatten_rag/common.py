from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pyspark.sql import SparkSession
from loguru import logger
from chatten.config import Config
from databricks.sdk import WorkspaceClient

T = TypeVar("T", bound=Config)


class Task(ABC, Generic[T]):
    config_class: T

    def __init__(self):
        self.spark: SparkSession = SparkSession.builder.getOrCreate()
        self.logger = logger
        self.config: T = self.config_class()
        self.client = WorkspaceClient()

    @abstractmethod
    def run(self):
        """Run the task"""

    @classmethod
    def entrypoint(cls):
        logger.info(f"Running {cls.__name__}")
        instance = cls()
        logger.info(f"Config: {instance.config.model_dump_json(indent=4)}")

        logger.info(f"Setting catalog to {instance.config.catalog}")
        instance.spark.sql(f"USE CATALOG {instance.config.catalog}")

        logger.info(f"Setting database to {instance.config.db}")
        instance.spark.sql(f"CREATE DATABASE IF NOT EXISTS {instance.config.db}")
        instance.spark.sql(f"USE DATABASE {instance.config.db}")

        logger.info(f"Setting the volume to {instance.config.volume}")
        instance.spark.sql(f"CREATE VOLUME IF NOT EXISTS {instance.config.volume}")

        instance.run()
        logger.info(f"Finished running {cls.__name__}")
