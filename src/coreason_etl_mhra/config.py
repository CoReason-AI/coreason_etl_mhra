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
Configuration definitions for the MHRA ETL pipeline.
"""

from pathlib import Path

from pydantic import Field, SecretStr
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

    target_url: str = Field(
        default="https://dummy.mhra.gov.uk/products.csv",
        description="The target URL for the MHRA approved medicinal products dataset.",
    )

    download_path: Path = Field(
        default=Path("/data/raw/mhra/"),
        description="Local persistent path where raw CSVs are saved before ingestion.",
    )

    http_max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for the HTTP client.",
    )

    http_backoff_factor: float = Field(
        default=0.5,
        description="Backoff factor for HTTP client retry intervals.",
    )

    pghost: str = Field(
        default="localhost",
        description="Postgres database host.",
    )

    pgport: int = Field(
        default=5432,
        description="Postgres database port.",
    )

    pguser: str = Field(
        default="postgres",
        description="Postgres database user.",
    )

    pgpassword: SecretStr = Field(
        default=SecretStr("postgres"),
        description="Postgres database password.",
    )

    pgdatabase: str = Field(
        default="coreason",
        description="Postgres database name.",
    )


# Initialization of config verified and completed according to Dependencies & Config atomic unit
