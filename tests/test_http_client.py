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
