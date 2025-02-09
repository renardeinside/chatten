import collections
from functools import partial
from pathlib import PosixPath
import requests
from chatten.config import Config
from chatten_rag.common import Task
from concurrent.futures import ThreadPoolExecutor
import io
from pypdf import PdfReader
from pyspark.sql.functions import pandas_udf, col, explode, expr
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter


@pandas_udf("string")
def extract_text_from_pdf(binary_content: pd.Series) -> pd.Series:
    def extract_text(pdf_bytes):
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = []
            for page in reader.pages:
                text.append(page.extract_text())

            final_text = "\n".join(text)

            if not final_text.replace("\n", "").strip():
                raise ValueError("Extracted text is empty or contains only whitespace.")

            return final_text
        except Exception as e:
            return f"_____PDF_PARSE_ERROR_____: {str(e)}"

    return binary_content.apply(extract_text)


@pandas_udf("array<string>")
def split_text(text: pd.Series) -> pd.Series:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    return text.apply(text_splitter.split_text)


class Loader(Task[Config]):
    config_class = Config

    def _download_file(self, url: str, destination: PosixPath) -> PosixPath:
        filename = PosixPath(url.split("/")[-1])
        local_filename = destination / filename

        if local_filename.exists():
            self.logger.info(f"File {local_filename} already exists. Skipping.")
            return local_filename

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            self.logger.info(f"Downloading {url} to {local_filename}")
            with local_filename.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    # if chunk:
                    f.write(chunk)
        return local_filename

    def download_file_from_git(self, dest: PosixPath, owner, repo, path):

        if not dest.exists():
            dest.mkdir(parents=True)

        files = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents{path}"
        ).json()
        files = [f["download_url"] for f in files if "NOTICE" not in f["name"]]
        files = [
            f.replace(
                "https://raw.githubusercontent.com/databricks-demos/dbdemos-dataset/main/",
                "https://dbdemos-dataset.s3.amazonaws.com/",
            )
            for f in files
        ]

        downloader = partial(self._download_file, destination=dest)

        with ThreadPoolExecutor(max_workers=10) as executor:
            collections.deque(executor.map(downloader, files))

    def process_files_into_table(self):
        source_path = "dbfs:" + self.config.full_raw_docs_path.as_posix()

        self.logger.info(
            f"Processing files into docs table {self.config.docs_full_name} from {source_path}"
        )

        df = (
            self.spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "BINARYFILE")
            .option("pathGlobFilter", "*.pdf")
            .load(source_path)
        )

        query = (
            df.withColumn("text", extract_text_from_pdf(col("content")))
            .where("text NOT LIKE '_____PDF_PARSE_ERROR%'")
            .withColumn("chunks", split_text(col("text")))
            .select("path", explode(col("chunks")).alias("chunk_text"))
            .withColumn("chunk_uuid", expr("uuid()"))  # add a unique id for each chunk
            .writeStream.trigger(availableNow=True)
            .option(
                "checkpointLocation",
                self.config.full_raw_docs_checkpoint_location,
            )
            .option("mergeSchema", "true")
            .toTable(self.config.docs_full_name)
        )

        query.awaitTermination()

        enable_cdf = f"""
        ALTER TABLE {self.config.docs_full_name} 
            SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
        """
        self.spark.sql(enable_cdf)

        self.logger.info(f"Finished processing files into {self.config.docs_full_name}")

    def run(self):
        self.logger.info(
            f"Downloading files from git into {self.config.full_raw_docs_path}"
        )
        self.download_file_from_git(
            self.config.full_raw_docs_path,
            "databricks-demos",
            "dbdemos-dataset",
            "/llm/databricks-pdf-documentation",
        )
        self.logger.info("Finished downloading files")

        self.process_files_into_table()
