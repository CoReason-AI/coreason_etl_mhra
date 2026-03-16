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
from unittest.mock import MagicMock

import pytest
import requests
from requests.exceptions import RequestException

from coreason_etl_mhra.config import RegulatoryIngestionManifest
from coreason_etl_mhra.ingestion.download import RegulatoryDownloadTask


@pytest.fixture
def mock_manifest(tmp_path: Path) -> RegulatoryIngestionManifest:
    """Fixture providing a configured manifest pointing to a temporary directory."""
    return RegulatoryIngestionManifest(
        target_url="https://dummy.mhra.gov.uk/data/products.csv",
        download_path=tmp_path / "raw" / "mhra",
    )


@pytest.fixture
def mock_session() -> MagicMock:
    """Fixture providing a mocked requests.Session."""
    return MagicMock(spec=requests.Session)


def test_successful_download(
    mock_manifest: RegulatoryIngestionManifest,
    mock_session: MagicMock,
) -> None:
    """Verify that a successful HTTP response writes to the correct file path."""
    task = RegulatoryDownloadTask(session=mock_session, manifest=mock_manifest)

    # Mock response to stream chunks
    mock_response = MagicMock(spec=requests.Response)
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"chunk1,", b"chunk2,", b"chunk3"]

    # Context manager setup for requests.get
    mock_session.get.return_value.__enter__.return_value = mock_response

    downloaded_path = task.execute()

    # Asserts
    assert downloaded_path.name == "products.csv"
    assert downloaded_path.parent == mock_manifest.download_path
    assert downloaded_path.exists()

    with downloaded_path.open("rb") as f:
        content = f.read()
    assert content == b"chunk1,chunk2,chunk3"

    mock_session.get.assert_called_once_with(mock_manifest.target_url, stream=True)


def test_download_failure_http_error(
    mock_manifest: RegulatoryIngestionManifest,
    mock_session: MagicMock,
) -> None:
    """Verify that a RequestException is raised on HTTP errors."""
    task = RegulatoryDownloadTask(session=mock_session, manifest=mock_manifest)

    # Mock an HTTP error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = RequestException("404 Not Found")
    mock_session.get.return_value.__enter__.return_value = mock_response

    with pytest.raises(RequestException, match="404 Not Found"):
        task.execute()


def test_download_fallback_filename(
    tmp_path: Path,
    mock_session: MagicMock,
) -> None:
    """Verify that a default filename is used if the URL path ends without one."""
    manifest = RegulatoryIngestionManifest(
        target_url="https://dummy.mhra.gov.uk/",
        download_path=tmp_path,
    )
    task = RegulatoryDownloadTask(session=mock_session, manifest=manifest)

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"empty"]
    mock_session.get.return_value.__enter__.return_value = mock_response

    downloaded_path = task.execute()

    assert downloaded_path.name == "mhra_products.csv"
    assert downloaded_path.exists()


def test_download_unexpected_error(
    mock_manifest: RegulatoryIngestionManifest,
    mock_session: MagicMock,
) -> None:
    """Verify that unexpected exceptions during execution are caught and raised."""
    task = RegulatoryDownloadTask(session=mock_session, manifest=mock_manifest)

    # Make get() raise a generic exception
    mock_session.get.side_effect = ValueError("Some unexpected configuration error")

    with pytest.raises(ValueError, match="Some unexpected configuration error"):
        task.execute()
