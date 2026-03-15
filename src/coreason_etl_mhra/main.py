# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra

"""
Main entry point and orchestration logic for the MHRA ETL pipeline.
"""

from coreason_etl_mhra.config import RegulatoryIngestionManifest
from coreason_etl_mhra.http_client import create_session
from coreason_etl_mhra.ingestion.download import RegulatoryDownloadTask
from coreason_etl_mhra.ingestion.pipeline import RegulatoryIngestionPipeline
from coreason_etl_mhra.utils.logger import logger


def run_pipeline() -> None:
    """
    Orchestrates the full MHRA pipeline.
    """
    logger.info("Starting MHRA ETL pipeline")

    manifest = RegulatoryIngestionManifest()

    try:
        # Step 1: Initialize dependencies
        logger.info("Step 1: Initializing configuration and HTTP client...")
        session = create_session(manifest)

        # Step 2: Download raw data
        logger.info("Step 2: Executing download task...")
        download_task = RegulatoryDownloadTask(session, manifest)
        file_path = download_task.execute()

        # Step 3: Execute ingestion pipeline
        logger.info("Step 3: Executing ingestion pipeline...")
        ingestion_pipeline = RegulatoryIngestionPipeline(manifest)
        ingestion_pipeline.run(file_path)

        logger.info("MHRA ETL pipeline completed successfully")

    except Exception as e:
        logger.exception("MHRA ETL pipeline failed", error=str(e))
        raise


if __name__ == "__main__":  # pragma: no cover
    run_pipeline()
