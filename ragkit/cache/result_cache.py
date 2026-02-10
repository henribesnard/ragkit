"""Result cache for retrieval outputs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ragkit.cache.backends import build_backend
from ragkit.cache.backends.base import CacheBackend
from ragkit.config.schema_v2 import CacheConfigV2


class ResultCache:
    """Cache for retrieval/reranking results."""

    def __init__(self, config: CacheConfigV2, backend: CacheBackend | None = None) -> None:
        self.config = config
        self.backend = backend or build_backend(
            config,
            size_mb=config.result_cache_size_mb,
            ttl=config.result_cache_ttl,
        )

    async def get(self, embedding: list[float]) -> Any | None:
        key = self._hash_embedding(embedding)
        return await self.backend.get(key)

    async def set(self, embedding: list[float], value: Any) -> None:
        key = self._hash_embedding(embedding)
        await self.backend.set(key, value, ttl=self.config.result_cache_ttl)

    async def clear(self) -> None:
        await self.backend.clear()

    @staticmethod
    def _hash_embedding(embedding: list[float]) -> str:
        rounded = [round(val, 6) for val in embedding]
        payload = json.dumps(rounded, sort_keys=True)
        return hashlib.md5(payload.encode("utf-8")).hexdigest()
