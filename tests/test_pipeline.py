# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_mhra_products

from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from coreason_etl_mhra_products.config import RegulatoryIngestionManifest
from coreason_etl_mhra_products.ingestion.pipeline import (
    NAMESPACE_COREASON,
    RegulatoryIngestionPipeline,
    _generate_uuidv5,
)


@pytest.fixture
def mock_manifest() -> RegulatoryIngestionManifest:
    """Fixture providing a mock manifest."""
    return RegulatoryIngestionManifest()


def test_generate_uuidv5() -> None:
    """Verify that _generate_uuidv5 generates deterministic UUIDs correctly."""
    s = pl.Series(["123", "456"])
    res = _generate_uuidv5(s)

    assert len(res) == 2
    # Check that they look like UUIDs and are consistent
    import uuid

    expected_1 = str(uuid.uuid5(NAMESPACE_COREASON, "123"))
    expected_2 = str(uuid.uuid5(NAMESPACE_COREASON, "456"))

    assert res[0] == expected_1
    assert res[1] == expected_2


@patch("coreason_etl_mhra_products.ingestion.pipeline.pl.read_excel")
def test_process_file_with_licence_number(
    mock_read_excel: MagicMock, mock_manifest: RegulatoryIngestionManifest
) -> None:
    """Verify processing when 'Licence Number' is present."""
    mock_df = pl.DataFrame(
        {
            "Licence Number": ["PL 123", "PL 456"],
            "Product Name": ["Drug A", "Drug B"],
        }
    )
    mock_read_excel.return_value = mock_df

    pipeline = RegulatoryIngestionPipeline(manifest=mock_manifest)
    file_path = Path("test_file.xlsx")

    results = list(pipeline._process_file(file_path))

    assert len(results) == 2
    assert results[0]["source_file"] == "test_file.xlsx"
    assert "ingestion_ts" in results[0]

    # Verify UUID generation
    import uuid

    expected_id_1 = str(uuid.uuid5(NAMESPACE_COREASON, "PL 123"))
    assert results[0]["coreason_id"] == expected_id_1
    assert results[0]["raw_data"]["Licence Number"] == "PL 123"
    assert results[0]["raw_data"]["Product Name"] == "Drug A"

    expected_id_2 = str(uuid.uuid5(NAMESPACE_COREASON, "PL 456"))
    assert results[1]["coreason_id"] == expected_id_2


@patch("coreason_etl_mhra_products.ingestion.pipeline.pl.read_excel")
def test_process_file_without_licence_number(
    mock_read_excel: MagicMock, mock_manifest: RegulatoryIngestionManifest
) -> None:
    """Verify fallback behavior when 'Licence Number' is missing."""
    mock_df = pl.DataFrame(
        {
            "Product Name": ["Drug A", "Drug B"],
        }
    )
    mock_read_excel.return_value = mock_df

    pipeline = RegulatoryIngestionPipeline(manifest=mock_manifest)
    file_path = Path("test_file.xlsx")

    results = list(pipeline._process_file(file_path))

    assert len(results) == 2
    assert results[0]["source_file"] == "test_file.xlsx"

    # UUID should be based on row_index ("0", "1")
    import uuid

    expected_id_1 = str(uuid.uuid5(NAMESPACE_COREASON, "0"))
    assert results[0]["coreason_id"] == expected_id_1
    assert results[0]["raw_data"]["Product Name"] == "Drug A"
    assert "row_index" not in results[0]["raw_data"]

    expected_id_2 = str(uuid.uuid5(NAMESPACE_COREASON, "1"))
    assert results[1]["coreason_id"] == expected_id_2
    assert results[1]["raw_data"]["Product Name"] == "Drug B"
    assert "row_index" not in results[1]["raw_data"]


@patch("coreason_etl_mhra_products.ingestion.pipeline.dlt.pipeline")
@patch("coreason_etl_mhra_products.ingestion.pipeline.RegulatoryIngestionPipeline._get_mhra_resource")
def test_pipeline_run(
    mock_get_resource: MagicMock,
    mock_dlt_pipeline: MagicMock,
    mock_manifest: RegulatoryIngestionManifest,
) -> None:
    """Verify pipeline.run configures and executes DLT correctly."""
    pipeline = RegulatoryIngestionPipeline(manifest=mock_manifest)

    mock_dlt_instance = MagicMock()
    mock_dlt_pipeline.return_value = mock_dlt_instance

    mock_resource = MagicMock()
    mock_get_resource.return_value = mock_resource

    pipeline.run(Path("test_file.xlsx"))

    # Assert DLT pipeline creation
    mock_dlt_pipeline.assert_called_once()
    kwargs = mock_dlt_pipeline.call_args.kwargs
    assert kwargs["pipeline_name"] == "mhra_products"
    assert kwargs["dataset_name"] == "bronze"
    assert kwargs["destination"]
    # we don't assert destination precisely here as it involves secret values, but it's passed

    # Assert get_resource call
    mock_get_resource.assert_called_once_with(Path("test_file.xlsx"))

    # Assert nesting limit is set to 0
    assert mock_resource.max_table_nesting == 0

    # Assert pipeline execution
    mock_dlt_instance.run.assert_called_once_with(mock_resource, loader_file_format="jsonl", schema_contract="evolve")


@patch("coreason_etl_mhra_products.ingestion.pipeline.dlt.resource")
def test_get_mhra_resource(mock_dlt_resource: MagicMock, mock_manifest: RegulatoryIngestionManifest) -> None:
    """Verify the creation of DLT resource."""
    pipeline = RegulatoryIngestionPipeline(manifest=mock_manifest)

    # Just to execute the wrapper, mock what dlt.resource does normally
    # dlt.resource is a decorator factory. Let's patch it just to see it gets called.
    decorator_mock = MagicMock()
    mock_dlt_resource.return_value = decorator_mock

    _ = pipeline._get_mhra_resource(Path("test.xlsx"))

    mock_dlt_resource.assert_called_once_with(
        name="coreason_etl_mhra_products_bronze_mhra_products_raw", write_disposition="merge", primary_key="coreason_id"
    )
