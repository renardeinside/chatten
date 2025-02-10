from pathlib import Path, PosixPath
import tempfile
from typing import Any
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


def log_agent(
    agent_path: str, model_config_path: str, input_example: dict[str, Any], vsi: str
) -> ModelInfo:
    return mlflow.langchain.log_model(
        lc_model=agent_path,
        model_config=model_config_path,
        pip_requirements=[
            "databricks-langchain",
            "langgraph",
            "langchain-core",
            "pydantic",
        ],
        artifact_path="agent",
        input_example=input_example,
        resources=[
            DatabricksVectorSearchIndex(
                index_name=vsi,
            ),
        ],
    )


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

        src_agent_path = Path(__file__).parent.parent / "agent.py"

        self.logger.info(f"Mlflow experiment set up: {experiment}")

        with tempfile.TemporaryDirectory() as _temp_dir:
            _temp_dir_path = PosixPath(_temp_dir)
            config_path = _temp_dir_path / "config.yml"
            dest_agent_path = _temp_dir_path / "agent.py"

            self.logger.info(
                f"Saving the agent and config to a temporary directory: {_temp_dir}"
            )

            dest_agent_path.write_text(src_agent_path.read_text())
            config_path.write_text(
                yaml.dump(
                    self.config.as_model_config,
                    indent=4,
                )
            )

            with mlflow.start_run(experiment_id=experiment.experiment_id) as run:
                self.logger.info(
                    f"Logging the agent to MLflow with name: {run.info.run_name}"
                )

                logged_agent_info = log_agent(
                    dest_agent_path.as_posix(),
                    config_path.as_posix(),
                    self.INPUT_EXAMPLE,
                    self.config.vsi_full_name,
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
