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

from pydantic import Field
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

    mhra_products_url: str = Field(
        default="https://dummy.mhra.gov.uk/products.csv",
        description="The target URL for the MHRA approved medicinal products dataset.",
    )

    download_dir: Path = Field(
        default=Path("/data/raw/mhra/"),
        description="Local persistent path where raw CSVs are saved before ingestion.",
    )
