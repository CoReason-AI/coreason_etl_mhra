# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra

from unittest.mock import MagicMock, patch

import pytest

from coreason_etl_mhra.main import run_pipeline


@patch("coreason_etl_mhra.main.create_session")
def test_run_pipeline_success(mock_create_session: MagicMock) -> None:
    """Verifies that the main pipeline orchestrates successfully."""
    mock_create_session.return_value = MagicMock()

    run_pipeline()

    # Verify order of execution
    mock_create_session.assert_called_once()


@patch("coreason_etl_mhra.main.create_session")
def test_run_pipeline_failure(mock_create_session: MagicMock) -> None:
    """Verifies that the main pipeline handles exceptions."""
    mock_create_session.side_effect = Exception("Config init failed")

    with pytest.raises(Exception, match=r"Config init failed"):
        run_pipeline()
