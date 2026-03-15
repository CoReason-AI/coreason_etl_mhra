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
Task for downloading the MHRA approved products dataset to local persistent storage.
"""

from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException

from coreason_etl_mhra.config import RegulatoryIngestionManifest
from coreason_etl_mhra.utils.logger import logger


class RegulatoryDownloadTask:
    """
    Task responsible for fetching the raw CSV payload from the MHRA endpoint
    and securing it to local persistent storage prior to ingestion.
    """

    def __init__(self, session: requests.Session, manifest: RegulatoryIngestionManifest) -> None:
        """
        Initializes the RegulatoryDownloadTask.

        Args:
            session: A configured HTTP session (e.g., with retries).
            manifest: The pipeline configuration containing URL and paths.
        """
        self._session = session
        self._manifest = manifest

    def execute(self) -> Path:
        """
        Executes the download process, streaming the response to disk in chunks.

        Returns:
            The Path to the successfully downloaded file on disk.

        Raises:
            requests.exceptions.RequestException: If the HTTP request fails.
            OSError: If there's an issue writing to the filesystem.
        """
        url = self._manifest.mhra_products_url
        download_dir = self._manifest.download_dir

        # Ensure directory exists
        download_dir.mkdir(parents=True, exist_ok=True)

        # Extract filename from URL, fallback to default if not present
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = "mhra_products.csv"

        target_path = download_dir / filename

        logger.info(
            "Starting MHRA download task",
            url=url,
            target_path=str(target_path),
        )

        try:
            with self._session.get(url, stream=True) as response:
                response.raise_for_status()

                with target_path.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

            logger.info("MHRA download task completed successfully", file_size=target_path.stat().st_size)
            return target_path

        except RequestException as e:
            logger.exception("HTTP error during MHRA download task", error=str(e), url=url)
            raise
        except Exception as e:
            logger.exception("Unexpected error during MHRA download task", error=str(e), target_path=str(target_path))
            raise
