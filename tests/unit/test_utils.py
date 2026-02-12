import asyncio

from ragkit.config.schema import LoggingConfig, MetricsConfig, ObservabilityConfig
from ragkit.models import Document
from ragkit.utils.async_utils import retry_async
from ragkit.utils.logging import setup_logging


def test_logging_setup() -> None:
    observability = ObservabilityConfig(
        logging=LoggingConfig(level="DEBUG"),
        metrics=MetricsConfig(enabled=False),
    )
    logger = setup_logging(observability)
    assert logger is not None


def test_retry_async() -> None:
    call_count = 0

    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary error")
        return "success"

    result = asyncio.run(retry_async(failing_func, max_retries=3, delay=0.01))
    assert result == "success"
    assert call_count == 3


def test_document_model() -> None:
    doc = Document(id="doc1", content="Test content", metadata={"source": "test.pdf"})
    assert doc.id == "doc1"
