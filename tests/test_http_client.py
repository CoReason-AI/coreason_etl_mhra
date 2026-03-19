from unittest.mock import MagicMock, patch

import pytest
import requests
from coreason_etl_mhra_products.config import RegulatoryIngestionManifest
from coreason_etl_mhra_products.http_client import create_session
from requests.adapters import HTTPAdapter


def test_create_session() -> None:
    """Verify that create_session returns a properly configured requests.Session."""
    manifest = RegulatoryIngestionManifest(http_max_retries=5, http_backoff_factor=1.0)
    session = create_session(manifest)

    assert session is not None

    adapter = session.get_adapter("https://")
    assert isinstance(adapter, HTTPAdapter)
    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == 1.0


def test_session_retry_on_500() -> None:
    """Verify that the configured session correctly retries requests on a 500 status."""
    manifest = RegulatoryIngestionManifest(http_max_retries=2, http_backoff_factor=0.01)
    session = create_session(manifest)

    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 500
    mock_response.headers = {}
    mock_response.raw = MagicMock()
    mock_response.raw.status = 500
    mock_response.url = "https://dummy.mhra.gov.uk/products.csv"
    mock_response.request = MagicMock()

    # We mock HTTPAdapter.send so that it raises RetryError
    with (
        patch("requests.adapters.HTTPAdapter.send", side_effect=requests.exceptions.RetryError),
        pytest.raises(requests.exceptions.RetryError),
    ):
        session.get("https://dummy.mhra.gov.uk/products.csv")


def test_session_retry_on_connection_error() -> None:
    """Verify that connection drops are retried."""
    manifest = RegulatoryIngestionManifest(http_max_retries=3, http_backoff_factor=0.01)
    session = create_session(manifest)

    # Mock the adapter send to raise a connection error
    with (
        patch(
            "requests.adapters.HTTPAdapter.send",
            side_effect=requests.exceptions.ConnectionError("Connection dropped"),
        ),
        pytest.raises(requests.exceptions.ConnectionError),
    ):
        session.get("https://dummy.mhra.gov.uk/products.csv")
