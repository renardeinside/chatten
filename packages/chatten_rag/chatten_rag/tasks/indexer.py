from chatten_rag.common import Task
from chatten.config import Config
from databricks.vector_search.client import VectorSearchClient


class IndexerConfig(Config):

    # vector search index
    vsi: str = "vsi"
    vsi_endpoint: str

    # embedding model endpoint
    embeddings_endpoint: str = "databricks-bge-large-en"

    @property
    def vsi_full_name(self):
        return f"{self.catalog}.{self.db}.{self.vsi}"

    @property
    def docs_full_name(self):
        return f"{self.catalog}.{self.db}.{self.docs_table}"


class Indexer(Task[IndexerConfig]):
    config_class = IndexerConfig

    def run(self):

        client = VectorSearchClient(disable_notice=True)

        self.logger.info(f"Checking the VSI endpoint {self.config.vsi_endpoint}")
        try:
            client.get_endpoint(self.config.vsi_endpoint)
            self.logger.info(f"Endpoint {self.config.vsi_endpoint} found.")
        except Exception:
            self.logger.info(
                f"Endpoint {self.config.vsi_endpoint} not found. Creating it."
            )

            client.create_endpoint_and_wait(
                name=self.config.vsi_endpoint,
            )

        self.logger.info(f"Checking the vsi index @ {self.config.vsi_full_name}")

        try:
            index = client.get_index(index_name=self.config.vsi_full_name)
            self.logger.info(f"Index {self.config.vsi} found.")
        except Exception:
            self.logger.info(
                f"Index {self.config.vsi} not found in {self.config.catalog}.{self.config.db} - creating it..."
            )

            index = client.create_delta_sync_index_and_wait(
                endpoint_name=self.config.vsi_endpoint,
                source_table_name=self.config.docs_full_name,
                index_name=self.config.vsi_full_name,
                pipeline_type="TRIGGERED",
                primary_key="path",
                embedding_source_column="text",
                embedding_model_endpoint_name=self.config.embeddings_endpoint,
                sync_computed_embeddings=True,
            )

        self.logger.info(
            f"Waiting for index {self.config.vsi_full_name} to be ready..."
        )
        index.wait_until_ready()

        self.logger.info(f"Index {self.config.vsi_full_name} is ready, syncing it...")
        index.sync()
        self.logger.info(f"Index {self.config.vsi_full_name} sync complete.")
