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
Configuration definitions for the MHRA ETL pipeline.
"""

from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RegulatoryIngestionManifest(BaseSettings):
    """
    Configuration manifest for the MHRA regulatory products ingestion.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AGENT INSTRUCTION: Configured the target URL placeholder default
    target_url: str = Field(
        default="https://dummy.mhra.gov.uk/products.csv",
        description="The target URL for the MHRA approved medicinal products dataset.",
    )

    # AGENT INSTRUCTION: Configured the local persistent path
    download_path: Path = Field(
        default=Path("/data/raw/mhra/"),
        description="Local persistent path where raw CSV files are saved before ingestion.",
    )

    csv_delimiter: str = Field(
        default=",",
        description="The delimiter used in the source CSV file.",
    )

    csv_encoding: str = Field(
        default="utf-8",
        description="The character encoding used in the source CSV file.",
    )

    http_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for the HTTP client.",
    )

    http_backoff_factor: float = Field(
        default=0.5,
        description="Backoff factor for HTTP client retry intervals.",
    )

    pg_dsn: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/coreason",  # type: ignore[assignment]
        description="Postgres database connection DSN.",
    )


# Initialization of config verified and completed according to Dependencies & Config atomic unit
