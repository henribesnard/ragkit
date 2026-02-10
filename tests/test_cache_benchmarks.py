"""Benchmark-style tests for cache performance."""

import asyncio
import time

import pytest

from ragkit.cache.batch_processor import BatchProcessor
from ragkit.cache.cache_manager import CacheManager
from ragkit.config.schema_v2 import CacheConfigV2


@pytest.mark.asyncio
async def test_cache_reduces_latency():
    config = CacheConfigV2(
        query_cache_enabled=True,
        embedding_cache_enabled=False,
        result_cache_enabled=False,
        cache_key_strategy="exact",
        cache_backend="memory",
    )
    manager = CacheManager(config)

    async def compute_fn(query: str):
        await asyncio.sleep(0.05)
        return f"answer:{query}"

    start = time.monotonic()
    await manager.get_or_compute("hello", compute_fn)
    cold_latency = time.monotonic() - start

    start = time.monotonic()
    await manager.get_or_compute("hello", compute_fn)
    warm_latency = time.monotonic() - start

    assert warm_latency < cold_latency * 0.3


@pytest.mark.asyncio
async def test_batching_improves_throughput():
    async def process_batch(items):
        await asyncio.sleep(0.05)
        return items

    processor = BatchProcessor(process_batch_fn=process_batch, batch_size=10, timeout_ms=50)
    items = [f"q{i}" for i in range(10)]

    start = time.monotonic()
    for item in items:
        await process_batch([item])
    sequential_time = time.monotonic() - start

    start = time.monotonic()
    results = await asyncio.gather(*[processor.process(item) for item in items])
    batched_time = time.monotonic() - start
    await processor.stop()

    assert results == items
    assert batched_time < sequential_time / 2
