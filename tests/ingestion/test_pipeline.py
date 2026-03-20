# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra_products

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl

from coreason_etl_mhra_products.config import RegulatoryIngestionManifest
from coreason_etl_mhra_products.ingestion.pipeline import (
    NAMESPACE_COREASON,
    RegulatoryIngestionPipeline,
    _generate_uuidv5,
)


def test_generate_uuidv5() -> None:
    """Verifies that the UUIDv5 generator works correctly."""
    series = pl.Series(["test1", "test2"])
    result = _generate_uuidv5(series)
    assert len(result) == 2
    assert result[0] == str(uuid.uuid5(NAMESPACE_COREASON, "test1"))
    assert result[1] == str(uuid.uuid5(NAMESPACE_COREASON, "test2"))


@patch("coreason_etl_mhra_products.ingestion.pipeline.pl.read_excel")
def test_process_file_with_licence_number(mock_read_excel: MagicMock, tmp_path: Path) -> None:
    """Verifies processing of an Excel file containing a Licence Number column."""
    manifest = RegulatoryIngestionManifest()
    pipeline = RegulatoryIngestionPipeline(manifest)

    mock_df = pl.DataFrame(
        {
            "Licence Number": ["PL 12345/0001", None],
            "Product Name": ["Aspirin", "Empty Licence"],
        }
    )
    mock_read_excel.return_value = mock_df

    excel_path = tmp_path / "test.xlsx"
    records = list(pipeline._process_file(excel_path))

    assert len(records) == 2

    # First record
    assert "coreason_id" in records[0]
    assert records[0]["coreason_id"] == str(uuid.uuid5(NAMESPACE_COREASON, "PL 12345/0001"))
    assert records[0]["source_file"] == "test.xlsx"
    assert "ingestion_ts" in records[0]
    assert records[0]["raw_data"] == {"Licence Number": "PL 12345/0001", "Product Name": "Aspirin"}

    # Second record (empty license)
    assert records[1]["coreason_id"] == str(uuid.uuid5(NAMESPACE_COREASON, ""))
    assert records[1]["raw_data"] == {"Licence Number": None, "Product Name": "Empty Licence"}


@patch("coreason_etl_mhra_products.ingestion.pipeline.pl.read_excel")
def test_process_file_without_licence_number(mock_read_excel: MagicMock, tmp_path: Path) -> None:
    """Verifies fallback UUID generation when Licence Number is missing."""
    manifest = RegulatoryIngestionManifest()
    pipeline = RegulatoryIngestionPipeline(manifest)

    mock_df = pl.DataFrame(
        {
            "Product Name": ["Aspirin"],
            "Active Substance": ["Acetylsalicylic acid"],
        }
    )
    mock_read_excel.return_value = mock_df

    excel_path = tmp_path / "test.xlsx"
    records = list(pipeline._process_file(excel_path))

    assert len(records) == 1
    assert "coreason_id" in records[0]
    # UUID should be based on row_index "0"
    assert records[0]["coreason_id"] == str(uuid.uuid5(NAMESPACE_COREASON, "0"))
    assert records[0]["raw_data"] == {"Product Name": "Aspirin", "Active Substance": "Acetylsalicylic acid"}


@patch("coreason_etl_mhra_products.ingestion.pipeline.pl.read_excel")
def test_get_mhra_resource(mock_read_excel: MagicMock, tmp_path: Path) -> None:
    """Verifies that the DLT resource generates records correctly."""
    manifest = RegulatoryIngestionManifest()
    pipeline = RegulatoryIngestionPipeline(manifest)

    mock_df = pl.DataFrame(
        {
            "Licence Number": ["PL 12345/0001"],
            "Product Name": ["Aspirin"],
        }
    )
    mock_read_excel.return_value = mock_df

    excel_path = tmp_path / "test.xlsx"

    resource = pipeline._get_mhra_resource(excel_path)
    records = list(resource)

    assert len(records) == 1
    assert "coreason_id" in records[0]
    assert records[0]["raw_data"] == {"Licence Number": "PL 12345/0001", "Product Name": "Aspirin"}


@patch("coreason_etl_mhra_products.ingestion.pipeline.pl.read_excel")
@patch("coreason_etl_mhra_products.ingestion.pipeline.dlt.pipeline")
def test_pipeline_run(mock_dlt_pipeline: MagicMock, mock_read_excel: MagicMock, tmp_path: Path) -> None:
    """Verifies that the run method orchestrates DLT correctly."""
    manifest = RegulatoryIngestionManifest()
    pipeline = RegulatoryIngestionPipeline(manifest)

    mock_df = pl.DataFrame(
        {
            "Licence Number": ["PL 12345/0001"],
            "Product Name": ["Aspirin"],
        }
    )
    mock_read_excel.return_value = mock_df

    excel_path = tmp_path / "test.xlsx"

    mock_pipeline_instance = MagicMock()
    mock_dlt_pipeline.return_value = mock_pipeline_instance

    pipeline.run(excel_path)

    # Ensure DLT pipeline was initialized
    mock_dlt_pipeline.assert_called_once_with(
        pipeline_name="mhra_products",
        destination=mock_dlt_pipeline.call_args.kwargs["destination"],
        dataset_name="bronze",
    )

    # Ensure pipeline.run was called
    mock_pipeline_instance.run.assert_called_once()

    # Verify max_table_nesting is 0 on the passed resource
    resource_passed = mock_pipeline_instance.run.call_args.args[0]
    assert resource_passed.max_table_nesting == 0
    assert mock_pipeline_instance.run.call_args.kwargs["loader_file_format"] == "jsonl"
    assert mock_pipeline_instance.run.call_args.kwargs["schema_contract"] == "evolve"
