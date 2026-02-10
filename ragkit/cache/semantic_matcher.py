"""Semantic matcher for query cache."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ragkit.config.schema_v2 import CacheConfigV2


@dataclass
class _SemanticEntry:
    embedding: list[float]
    expires_at: float | None


Embedder = Callable[[list[str]], Awaitable[list[list[float]]] | list[list[float]]]


class SemanticMatcher:
    """Match queries by embedding similarity."""

    def __init__(self, config: CacheConfigV2, embedder: Embedder) -> None:
        self.config = config
        self.embedder = embedder
        self._store: dict[str, _SemanticEntry] = {}
        self._lock = asyncio.Lock()

    async def find(self, query: str) -> str | None:
        embedding = await self._embed(query)
        if not embedding:
            return None

        now = time.monotonic()
        best_key = None
        best_score = 0.0
        async with self._lock:
            expired = [key for key, entry in self._store.items() if entry.expires_at and entry.expires_at < now]
            for key in expired:
                self._store.pop(key, None)

            for key, entry in self._store.items():
                score = _cosine_similarity(embedding, entry.embedding)
                if score > best_score:
                    best_score = score
                    best_key = key

        if best_key and best_score >= self.config.semantic_cache_threshold:
            return best_key
        return None

    async def add(self, key: str, query: str, ttl: int | None) -> None:
        embedding = await self._embed(query)
        if not embedding:
            return
        expires_at = None
        if ttl and ttl > 0:
            expires_at = time.monotonic() + ttl
        async with self._lock:
            self._store[key] = _SemanticEntry(embedding=embedding, expires_at=expires_at)

    async def _embed(self, query: str) -> list[float]:
        result = self.embedder([query])
        if asyncio.iscoroutine(result):
            result = await result
        if not result:
            return []
        return list(result[0])


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
