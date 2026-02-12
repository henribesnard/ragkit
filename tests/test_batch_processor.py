"""Tests for batch processor."""

import asyncio

import pytest

from ragkit.cache.batch_processor import BatchProcessor


@pytest.mark.asyncio
async def test_batch_processor_batches_requests():
    batches = []

    async def process_batch(items):
        batches.append(list(items))
        return [item.upper() for item in items]

    processor = BatchProcessor(process_batch_fn=process_batch, batch_size=5, timeout_ms=50)

    task1 = asyncio.create_task(processor.process("a"))
    task2 = asyncio.create_task(processor.process("b"))
    results = await asyncio.gather(task1, task2)

    assert results == ["A", "B"]
    assert len(batches) == 1
    assert batches[0] == ["a", "b"]

    await processor.stop()
