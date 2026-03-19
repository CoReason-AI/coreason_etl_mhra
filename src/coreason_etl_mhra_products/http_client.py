"""
HTTP client components for the MHRA ETL pipeline.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from coreason_etl_mhra_products.config import RegulatoryIngestionManifest


def create_session(manifest: RegulatoryIngestionManifest) -> requests.Session:
    """
    Creates and configures a requests.Session with retry logic.

    Args:
        manifest: The configuration manifest containing retry parameters.

    Returns:
        A configured requests.Session instance.
    """
    session = requests.Session()

    retry_strategy = Retry(
        total=manifest.http_max_retries,
        backoff_factor=manifest.http_backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session
