from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pyspark.sql import SparkSession
from loguru import logger
from chatten.config import Config

T = TypeVar("T", bound=Config)


class Task(ABC, Generic[T]):
    config_class: T

    def __init__(self):
        self.spark: SparkSession = SparkSession.builder.getOrCreate()
        self.logger = logger
        self.config: T = self.config_class()

    @abstractmethod
    def run(self):
        """Run the task"""

    @classmethod
    def entrypoint(cls):
        logger.info(f"Running {cls.__name__}")
        instance = cls()
        logger.info(f"Config: {instance.config}")

        logger.info("Setting catalog to {instance.config.catalog}")
        instance.spark.sql(f"USE CATALOG {instance.config.catalog}")

        logger.info("Setting database to {instance.config.db}")
        instance.spark.sql(f"USE SCHEMA {instance.config.db}")

        instance.run()
        logger.info(f"Finished running {cls.__name__}")
