from chatten_rag.common import Task
from chatten.config import Config
from databricks.vector_search.client import VectorSearchClient


class IndexerConfig(Config):

    # vector search index
    vsi: str = "vsi"
    vsi_endpoint: str

    # embedding model endpoint
    embeddings_endpoint: str = "databricks-bge-large-en"


class Indexer(Task[IndexerConfig]):
    config_class = IndexerConfig

    def run(self):

        client = VectorSearchClient()

        try:
            client.get_endpoint(self.config.vsi_endpoint)
        except Exception:
            self.logger.info(
                f"Endpoint {self.config.vsi_endpoint} not found. Creating it."
            )

            client.create_endpoint_and_wait(
                name=self.config.vsi_endpoint,
            )

        try:
            index = client.get_index(
                index_name=f"{self.config.catalog}.{self.config.db}.{self.config.vsi}",
            )
        except Exception:
            self.logger.info(
                f"Index {self.config.vsi} not found in {self.config.catalog}.{self.config.db}. Creating it."
            )

            index = client.create_delta_sync_index_and_wait(
                endpoint_name=self.config.vsi_endpoint,
                source_table_name=f"{self.config.catalog}.{self.config.db}.{self.config.docs_table}",
                index_name=f"{self.config.catalog}.{self.config.db}.{self.config.vsi}",
                pipeline_type="TRIGGERED",
                primary_key="path",
                embedding_source_column="text",
                embedding_model_endpoint_name=self.config.embeddings_endpoint,
                sync_computed_embeddings=True,
            )

        index.sync()
