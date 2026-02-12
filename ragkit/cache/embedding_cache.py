"""Embedding cache."""

from __future__ import annotations

import hashlib

from ragkit.cache.backends import build_backend
from ragkit.cache.backends.base import CacheBackend
from ragkit.config.schema_v2 import CacheConfigV2


class EmbeddingCache:
    """Cache for embedding vectors."""

    def __init__(self, config: CacheConfigV2, backend: CacheBackend | None = None) -> None:
        self.config = config
        self.backend = backend or build_backend(
            config,
            size_mb=config.embedding_cache_size_mb,
            ttl=config.embedding_cache_ttl,
        )

    async def get(self, text: str) -> list[float] | None:
        key = self._hash_text(text)
        return await self.backend.get(key)

    async def set(self, text: str, embedding: list[float]) -> None:
        key = self._hash_text(text)
        await self.backend.set(key, embedding, ttl=self.config.embedding_cache_ttl)

    async def clear(self) -> None:
        await self.backend.clear()

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()
