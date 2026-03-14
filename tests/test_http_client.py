# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from coreason_etl_mhra.config import RegulatoryIngestionManifest
from coreason_etl_mhra.http_client import create_session


def test_create_session_configures_retries() -> None:
    """Verify that create_session configures the requests.Session with the manifest's retry settings."""
    manifest = RegulatoryIngestionManifest(
        http_max_retries=5,
        http_backoff_factor=1.5,
    )

    session = create_session(manifest)

    # Check that HTTPAdapter is mounted for both http and https
    http_adapter = session.get_adapter("http://")
    https_adapter = session.get_adapter("https://")

    assert isinstance(http_adapter, HTTPAdapter)
    assert isinstance(https_adapter, HTTPAdapter)

    # Check that the max_retries is a Retry object with the correct settings
    assert isinstance(http_adapter.max_retries, Retry)
    assert http_adapter.max_retries.total == 5
    assert http_adapter.max_retries.backoff_factor == 1.5
    assert http_adapter.max_retries.status_forcelist is not None
    assert set(http_adapter.max_retries.status_forcelist) == {429, 500, 502, 503, 504}
    assert http_adapter.max_retries.allowed_methods is not None
    assert set(http_adapter.max_retries.allowed_methods) == {"HEAD", "GET", "OPTIONS"}

    assert isinstance(https_adapter.max_retries, Retry)
    assert https_adapter.max_retries.total == 5
    assert https_adapter.max_retries.backoff_factor == 1.5
    assert https_adapter.max_retries.status_forcelist is not None
    assert set(https_adapter.max_retries.status_forcelist) == {429, 500, 502, 503, 504}
    assert https_adapter.max_retries.allowed_methods is not None
    assert set(https_adapter.max_retries.allowed_methods) == {"HEAD", "GET", "OPTIONS"}


def test_create_session_defaults() -> None:
    """Verify that create_session uses the default settings when not overridden."""
    manifest = RegulatoryIngestionManifest()

    session = create_session(manifest)
    http_adapter = session.get_adapter("http://")

    assert isinstance(http_adapter, HTTPAdapter)
    assert isinstance(http_adapter.max_retries, Retry)
    assert http_adapter.max_retries.total == 3
    assert http_adapter.max_retries.backoff_factor == 0.5
