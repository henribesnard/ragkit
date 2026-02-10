"""Tests for semantic query cache matching."""

import pytest

from ragkit.cache.query_cache import QueryCache
from ragkit.cache.semantic_matcher import SemanticMatcher
from ragkit.config.schema_v2 import CacheConfigV2


@pytest.mark.asyncio
async def test_semantic_cache_hits_similar_queries():
    config = CacheConfigV2(
        cache_key_strategy="semantic",
        semantic_cache_threshold=0.9,
        cache_backend="memory",
    )

    async def embedder(texts):
        mapping = {
            "how to secure api?": [1.0, 0.0],
            "how to protect api endpoints?": [0.95, 0.05],
        }
        return [mapping.get(text.lower(), [0.0, 1.0]) for text in texts]

    matcher = SemanticMatcher(config, embedder=embedder)
    cache = QueryCache(config, semantic_matcher=matcher)

    await cache.set("How to secure API?", "answer-1")
    cached = await cache.get("How to protect API endpoints?")

    assert cached == "answer-1"
