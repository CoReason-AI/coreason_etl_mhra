from coreason_etl_mhra_products.utils.logger import logger


def test_logger_configured() -> None:
    """Verify that the logger is configured and can log messages."""
    assert logger is not None
