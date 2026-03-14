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
HTTP client components for the MHRA ETL pipeline.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from coreason_etl_mhra.config import RegulatoryIngestionManifest


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
