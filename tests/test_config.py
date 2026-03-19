# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra_products
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_etl_mhra_products.config import RegulatoryIngestionManifest


def test_manifest_defaults() -> None:
    """Verify the default values of RegulatoryIngestionManifest."""
    manifest = RegulatoryIngestionManifest()
    assert manifest.target_url == "https://dummy.mhra.gov.uk/products.csv"
    assert manifest.download_path == Path("/data/raw/mhra/")
    assert manifest.http_max_retries == 3
    assert manifest.http_backoff_factor == 0.5
    assert manifest.pghost == "localhost"
    assert manifest.pgport == 5432
    assert manifest.pguser == "postgres"
    assert manifest.pgpassword.get_secret_value() == "postgres"
    assert manifest.pgdatabase == "coreason"


def test_manifest_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that environment variables can override the manifest configuration."""
    custom_url = "https://custom.mhra.gov.uk/data.csv"
    custom_dir = "/custom/data/raw/"

    monkeypatch.setenv("TARGET_URL", custom_url)
    monkeypatch.setenv("DOWNLOAD_PATH", custom_dir)
    monkeypatch.setenv("HTTP_MAX_RETRIES", "10")
    monkeypatch.setenv("HTTP_BACKOFF_FACTOR", "2.0")
    monkeypatch.setenv("PGHOST", "db.example.com")
    monkeypatch.setenv("PGPORT", "5433")
    monkeypatch.setenv("PGUSER", "admin")
    monkeypatch.setenv("PGPASSWORD", "secret")
    monkeypatch.setenv("PGDATABASE", "mhra_db")

    manifest = RegulatoryIngestionManifest()

    assert manifest.target_url == custom_url
    assert manifest.download_path == Path(custom_dir)
    assert manifest.http_max_retries == 10
    assert manifest.http_backoff_factor == 2.0
    assert manifest.pghost == "db.example.com"
    assert manifest.pgport == 5433
    assert manifest.pguser == "admin"
    assert manifest.pgpassword.get_secret_value() == "secret"
    assert manifest.pgdatabase == "mhra_db"


@given(url=st.text(min_size=1), dir_path=st.text(min_size=1))
def test_manifest_with_hypothesis(url: str, dir_path: str) -> None:
    """Verify manifest can take various string inputs for initialization via kwargs."""
    manifest = RegulatoryIngestionManifest(target_url=url, download_path=Path(dir_path))
    assert manifest.target_url == url
    assert manifest.download_path == Path(dir_path)


def test_manifest_invalid_types() -> None:
    """Verify that type coercion or validation errors occur for invalid types."""
    with pytest.raises(ValidationError):
        RegulatoryIngestionManifest(http_max_retries="not_an_int")

    with pytest.raises(ValidationError):
        RegulatoryIngestionManifest(http_backoff_factor="not_a_float")

    with pytest.raises(ValidationError):
        RegulatoryIngestionManifest(pgport="invalid_port")
