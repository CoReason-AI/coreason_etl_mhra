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


def test_manifest_port_boundaries() -> None:
    """Verify that port numbers outside the 1-65535 range are rejected."""
    # Valid boundaries
    assert RegulatoryIngestionManifest(pgport=1).pgport == 1
    assert RegulatoryIngestionManifest(pgport=65535).pgport == 65535

    # Invalid boundaries
    with pytest.raises(ValidationError) as exc:
        RegulatoryIngestionManifest(pgport=0)
    assert "Input should be greater than or equal to 1" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        RegulatoryIngestionManifest(pgport=65536)
    assert "Input should be less than or equal to 65535" in str(exc.value)


def test_manifest_secret_str_repr() -> None:
    """Verify that the secret representation doesn't leak the actual password."""
    manifest = RegulatoryIngestionManifest(pgpassword="super_secret_db_password_123")
    repr_str = repr(manifest)

    # Password should be masked
    assert "super_secret_db_password_123" not in repr_str
    assert "**********" in repr_str


def test_manifest_custom_retry_strategy() -> None:
    """Verify that custom retry configurations are properly instantiated."""
    manifest = RegulatoryIngestionManifest(http_max_retries=10, http_backoff_factor=3.14159)
    assert manifest.http_max_retries == 10
    assert manifest.http_backoff_factor == 3.14159
