from pathlib import Path

import pytest
from coreason_etl_mhra_products.config import RegulatoryIngestionManifest
from pydantic import ValidationError


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


def test_manifest_invalid_types() -> None:
    """Verify that type coercion or validation errors occur for invalid types."""
    with pytest.raises(ValidationError):
        RegulatoryIngestionManifest(http_max_retries="not_an_int")

    with pytest.raises(ValidationError):
        RegulatoryIngestionManifest(http_backoff_factor="not_a_float")

    with pytest.raises(ValidationError):
        RegulatoryIngestionManifest(pgport="invalid_port")
