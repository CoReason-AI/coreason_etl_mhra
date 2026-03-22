# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra_products

"""
Pipeline logic for processing the raw MHRA Excel and yielding it via DLT.
"""

import datetime
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt
import polars as pl
from dlt.destinations import postgres

from coreason_etl_mhra_products.config import RegulatoryIngestionManifest
from coreason_etl_mhra_products.utils.logger import logger

NAMESPACE_COREASON = uuid.UUID("3f8c5c7e-90f1-419b-a010-8b1b51d451a9")


def _generate_uuidv5(s: pl.Series) -> pl.Series:
    """
    AGENT INSTRUCTION: Helper function for Polars `map_batches` to vectorize UUIDv5 generation.
    """
    return pl.Series([str(uuid.uuid5(NAMESPACE_COREASON, str(val))) for val in s])


class RegulatoryIngestionPipeline:
    """
    Manages the reading of raw Excel files, UUID generation via Polars, and
    loading into the database via DLT.
    """

    def __init__(self, manifest: RegulatoryIngestionManifest) -> None:
        """
        Initializes the pipeline with the provided configuration.
        """
        self._manifest = manifest

    def _process_file(self, file_path: Path) -> Iterator[dict[str, Any]]:
        """
        Reads the Excel file using Polars, generates a UUIDv5 `coreason_id`,
        and yields each row wrapped in a 'raw_data' dictionary.
        """
        logger.info("Processing file via Polars", file_path=str(file_path))

        # We process the Excel file using read_excel
        # MHRA product file has a "Licence Number" column we use for identity
        df = pl.read_excel(file_path, engine="openpyxl")

        if "Licence Number" not in df.columns:
            logger.warning("File is missing 'Licence Number' column. UUID generation might fall back to row index.")
            # Fallback identity if Licence Number is missing
            df = df.with_row_index("row_index")
            df = df.with_columns(pl.col("row_index").cast(pl.Utf8).map_batches(_generate_uuidv5).alias("coreason_id"))
        else:
            df = df.with_columns(
                pl.col("Licence Number").fill_null("").cast(pl.Utf8).map_batches(_generate_uuidv5).alias("coreason_id")
            )

        filename = file_path.name
        ingestion_ts = datetime.datetime.now(datetime.UTC).isoformat()

        # Iterate over rows as dictionaries
        for row in df.iter_rows(named=True):
            coreason_id = row.pop("coreason_id")
            if "row_index" in row:
                row.pop("row_index")

            yield {
                "coreason_id": coreason_id,
                "source_file": filename,
                "ingestion_ts": ingestion_ts,
                "raw_data": row,
            }

    def _get_mhra_resource(self, file_path: Path) -> dlt.sources.DltResource:
        """
        DLT resource definition that wraps the file processing generator.
        """

        @dlt.resource(
            name="coreason_etl_mhra_products_bronze_mhra_products_raw",
            write_disposition="merge",
            primary_key="coreason_id",
        )
        def mhra_resource() -> Iterator[dict[str, Any]]:
            yield from self._process_file(file_path)

        return mhra_resource()

    def run(self, file_path: Path) -> None:
        """
        Executes the ingestion pipeline for the specified file.
        """
        logger.info("Starting DLT pipeline execution")

        # Configure dlt pipeline
        pipeline = dlt.pipeline(
            pipeline_name="mhra_products",
            destination=postgres(self._manifest.pg_dsn.unicode_string()),
            dataset_name="bronze",
        )

        # AGENT INSTRUCTION: Configure max_table_nesting=0 to prevent schema shredding
        # Ensure all nested structures remain as JSONB.

        # apply dlt resource with specific parameters
        resource = self._get_mhra_resource(file_path)
        resource.max_table_nesting = 0

        pipeline.run(resource, loader_file_format="jsonl", schema_contract="evolve")
        logger.info("DLT pipeline execution completed successfully")
