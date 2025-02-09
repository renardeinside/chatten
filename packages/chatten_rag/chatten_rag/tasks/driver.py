# Log the model to MLflow
from chatten_rag.agent import get_agent
from chatten_rag.common import Task
import mlflow
from mlflow.models.resources import (
    DatabricksVectorSearchIndex,
)
from mlflow.models.model import ModelInfo

from chatten.config import Config
from databricks import agents


class Driver(Task[Config]):
    config_class = Config

    INPUT_EXAMPLE = {
        "messages": [{"role": "user", "content": "What is Unity Catalog?"}]
    }

    def run(self):
        agent = get_agent(self.config)

        with mlflow.start_run():
            logged_agent_info: ModelInfo = mlflow.langchain.log_model(
                lc_model=agent,
                pip_requirements=[
                    "databricks-langchain",
                    "langgraph",
                    "langchain-core",
                    "pydantic",
                    "pydantic-settings",
                    "loguru",
                ],
                model_config="config.yml",
                artifact_path="agent",
                input_example=self.INPUT_EXAMPLE,
                resources=[
                    DatabricksVectorSearchIndex(
                        index_name=self.config.vsi_full_name,
                    ),
                ],
                infer_code_paths=True,  # Enabling automatic code dependency inference to save chatten code
            )

        self.logger.info(f"Model logged to MLflow: {logged_agent_info}")

        # Register the model with the UC registry
        mlflow.set_registry_uri("databricks-uc")

        self.logger.info(
            f"Registering the model with the UC registry: {self.config.agent_serving_endpoint_full}"
        )
        registered_model_info = mlflow.register_model(
            logged_agent_info.model_uri, self.config.agent_serving_endpoint_full
        )

        self.logger.info("Creating the agent serving endpoint")
        result = agents.deploy(
            self.config.agent_serving_endpoint_full, registered_model_info.version
        )

        self.logger.info(
            f"Agent serving endpoint created with name: {result.endpoint_name}"
        )
