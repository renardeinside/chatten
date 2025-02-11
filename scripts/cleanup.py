from chatten.config import Config
from databricks.sdk import WorkspaceClient
from loguru import logger


def main():
    config = Config()

    logger.warning("Cleaning up the chatten artifacts, with config:")
    logger.warning(config.model_dump_json(indent=4))

    client = WorkspaceClient(profile=config.profile)

    logger.info(f"Deleting the docs table: {config.docs_with_catalog}")
    try:
        client.tables.delete(config.docs_with_catalog)
    except Exception as e:
        logger.error(f"Error deleting the docs table: {e}")

    logger.info(f"Deleting the vector search index: {config.vsi_with_catalog}")
    try:
        client.vector_search_indexes.delete_index(config.vsi_with_catalog)
    except Exception as e:
        logger.error(f"Error deleting the vector search index: {e}")


if __name__ == "__main__":
    main()
