import pytest

from ragkit.embedding.base import BaseEmbedder
from ragkit.embedding.cache import CachedEmbedder, EmbeddingCache


class DummyEmbedder(BaseEmbedder):
    def __init__(self) -> None:
        self.call_count = 0

    @property
    def dimensions(self):
        return 3

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [[1.0, 0.0, 0.0] for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        self.call_count += 1
        return [0.5, 0.5, 0.5]


@pytest.mark.asyncio
async def test_embedding_cache_memory():
    cache = EmbeddingCache(backend="memory", ttl=3600)
    embedder = DummyEmbedder()
    cached = CachedEmbedder(embedder, cache)

    result1 = await cached.embed(["text1"])
    assert result1[0] == [1.0, 0.0, 0.0]
    assert embedder.call_count == 1

    result2 = await cached.embed(["text1"])
    assert result2[0] == [1.0, 0.0, 0.0]
    assert embedder.call_count == 1


@pytest.mark.asyncio
async def test_embedding_cache_query():
    cache = EmbeddingCache(backend="memory", ttl=3600)
    embedder = DummyEmbedder()
    cached = CachedEmbedder(embedder, cache)

    result1 = await cached.embed_query("query")
    assert result1 == [0.5, 0.5, 0.5]
    assert embedder.call_count == 1

    result2 = await cached.embed_query("query")
    assert result2 == [0.5, 0.5, 0.5]
    assert embedder.call_count == 1
