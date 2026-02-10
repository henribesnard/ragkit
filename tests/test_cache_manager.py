"""Tests for cache manager orchestration."""

import pytest

from ragkit.cache.cache_manager import CacheManager
from ragkit.config.schema_v2 import CacheConfigV2


@pytest.mark.asyncio
async def test_cache_manager_query_cache_hit():
    config = CacheConfigV2(
        query_cache_enabled=True,
        embedding_cache_enabled=False,
        result_cache_enabled=False,
        cache_key_strategy="exact",
        query_cache_ttl=3600,
        cache_backend="memory",
    )
    manager = CacheManager(config)
    calls = {"count": 0}

    async def compute_fn(query: str):
        calls["count"] += 1
        return f"answer:{query}"

    first = await manager.get_or_compute("hello", compute_fn)
    second = await manager.get_or_compute("hello", compute_fn)

    assert first == "answer:hello"
    assert second == "answer:hello"
    assert calls["count"] == 1
    assert manager.metrics.hit_rate("query_cache") == 0.5


@pytest.mark.asyncio
async def test_cache_manager_embedding_cache_hit():
    config = CacheConfigV2(
        query_cache_enabled=False,
        embedding_cache_enabled=True,
        result_cache_enabled=False,
        cache_backend="memory",
    )
    manager = CacheManager(config)
    embed_calls = {"count": 0}

    async def embed_fn(query: str):
        embed_calls["count"] += 1
        return [1.0, 0.0]

    async def compute_fn(query: str, embedding=None):
        return embedding

    first = await manager.get_or_compute("q", compute_fn, embed_fn=embed_fn)
    second = await manager.get_or_compute("q", compute_fn, embed_fn=embed_fn)

    assert first == [1.0, 0.0]
    assert second == [1.0, 0.0]
    assert embed_calls["count"] == 1


@pytest.mark.asyncio
async def test_cache_metrics_latency_and_cost_saved():
    config = CacheConfigV2(
        query_cache_enabled=True,
        embedding_cache_enabled=False,
        result_cache_enabled=False,
        cache_key_strategy="exact",
        cache_backend="memory",
    )
    manager = CacheManager(config)

    async def compute_fn(query: str):
        return "answer"

    await manager.get_or_compute(
        "q",
        compute_fn,
        latency_estimates={"query_cache": 100.0},
        cost_estimates={"query_cache": 0.02},
    )
    await manager.get_or_compute(
        "q",
        compute_fn,
        latency_estimates={"query_cache": 100.0},
        cost_estimates={"query_cache": 0.02},
    )

    assert manager.metrics.latency_saved_total_ms() == 100.0
    assert manager.metrics.cost_saved_total_usd() == 0.02
