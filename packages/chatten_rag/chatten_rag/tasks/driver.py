from pathlib import Path
import tempfile
from chatten_rag.common import Task
import mlflow
from mlflow.models.resources import (
    DatabricksVectorSearchIndex,
)
from mlflow.models.model import ModelInfo
import yaml

from chatten.config import Config
from databricks import agents
from databricks.sdk import WorkspaceClient


class Driver(Task[Config]):
    config_class = Config

    INPUT_EXAMPLE = {
        "messages": [{"role": "user", "content": "What is Unity Catalog?"}]
    }

    def run(self):
        self.logger.info("Setting up the MLflow experiment")

        username = WorkspaceClient().current_user.me().user_name
        experiment_path = f"/Users/{username}/chatten"
        experiment = mlflow.set_experiment(experiment_path)

        self.logger.info(f"Mlflow experiment set up: {experiment}")

        with tempfile.NamedTemporaryFile() as temp_file:
            _config = yaml.dump(
                {
                    "chat_endpoint": self.config.chat_endpoint,
                    "vsi": self.config.vsi_full_name,
                    "PROMPT": self.config.PROMPT,
                },
                indent=4,
            )
            temp_file.write(_config.encode())

            with mlflow.start_run(experiment_id=experiment.experiment_id) as run:
                self.logger.info(
                    f"Logging the agent to MLflow with name: {run.info.run_name}"
                )

                agent_path = (
                    (Path(__file__).parent.parent / "agent.py").resolve().as_posix()
                )

                self.logger.info(
                    f"Saving agent using source path: {agent_path} with config path: {temp_file.name}"
                )

                logged_agent_info: ModelInfo = mlflow.langchain.log_model(
                    lc_model=agent_path,
                    model_config=temp_file.name,  # Path to the model config file
                    pip_requirements=[
                        "databricks-langchain",
                        "langgraph",
                        "langchain-core",
                        "pydantic",
                    ],
                    artifact_path="agent",
                    input_example=self.INPUT_EXAMPLE,
                    resources=[
                        DatabricksVectorSearchIndex(
                            index_name=self.config.vsi_full_name,
                        ),
                    ],
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
