# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_etl_mhra.config import RegulatoryIngestionManifest


def test_manifest_defaults() -> None:
    """Verify the default values of RegulatoryIngestionManifest."""
    manifest = RegulatoryIngestionManifest()
    assert manifest.mhra_products_url == "https://dummy.mhra.gov.uk/products.csv"
    assert manifest.download_dir == Path("/data/raw/mhra/")
    assert manifest.http_max_retries == 3
    assert manifest.http_backoff_factor == 0.5


def test_manifest_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that environment variables can override the manifest configuration."""
    custom_url = "https://custom.mhra.gov.uk/data.csv"
    custom_dir = "/custom/data/raw/"

    monkeypatch.setenv("MHRA_PRODUCTS_URL", custom_url)
    monkeypatch.setenv("DOWNLOAD_DIR", custom_dir)
    monkeypatch.setenv("HTTP_MAX_RETRIES", "10")
    monkeypatch.setenv("HTTP_BACKOFF_FACTOR", "2.0")

    manifest = RegulatoryIngestionManifest()

    assert manifest.mhra_products_url == custom_url
    assert manifest.download_dir == Path(custom_dir)
    assert manifest.http_max_retries == 10
    assert manifest.http_backoff_factor == 2.0


@given(url=st.text(min_size=1), dir_path=st.text(min_size=1))  # type: ignore[misc]
def test_manifest_with_hypothesis(url: str, dir_path: str) -> None:
    """Verify manifest can take various string inputs for initialization via kwargs."""
    manifest = RegulatoryIngestionManifest(mhra_products_url=url, download_dir=Path(dir_path))
    assert manifest.mhra_products_url == url
    assert manifest.download_dir == Path(dir_path)
