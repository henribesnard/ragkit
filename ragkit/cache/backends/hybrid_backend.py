"""Hybrid cache backend: hot memory, warm Redis."""

from __future__ import annotations

from typing import Any

from ragkit.cache.backends.memory_backend import MemoryBackend
from ragkit.cache.backends.redis_backend import RedisBackend


class HybridBackend:
    """Hybrid backend with in-memory LRU and Redis fallback."""

    def __init__(
        self,
        memory_backend: MemoryBackend,
        redis_backend: RedisBackend,
    ) -> None:
        self.memory_backend = memory_backend
        self.redis_backend = redis_backend

    async def get(self, key: str) -> Any | None:
        value = await self.memory_backend.get(key)
        if value is not None:
            return value
        value = await self.redis_backend.get(key)
        if value is not None:
            await self.memory_backend.set(key, value, ttl=None)
        return value

    async def set(self, key: str, value: Any, ttl: int | None) -> None:
        await self.memory_backend.set(key, value, ttl)
        await self.redis_backend.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self.memory_backend.delete(key)
        await self.redis_backend.delete(key)

    async def clear(self) -> None:
        await self.memory_backend.clear()
        await self.redis_backend.clear()
