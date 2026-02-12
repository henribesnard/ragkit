"""Cache backend factories."""

from __future__ import annotations

from ragkit.cache.backends.base import CacheBackend
from ragkit.cache.backends.hybrid_backend import HybridBackend
from ragkit.cache.backends.memory_backend import MemoryBackend
from ragkit.cache.backends.redis_backend import RedisBackend
from ragkit.config.schema_v2 import CacheConfigV2


def build_backend(
    config: CacheConfigV2,
    size_mb: int,
    ttl: int | None,
) -> CacheBackend:
    max_items = _estimate_max_items(size_mb)
    memory_backend = MemoryBackend(max_items=max_items, default_ttl=ttl)

    if config.cache_backend == "memory":
        return memory_backend

    redis_url = config.redis_url or "redis://localhost:6379/0"
    redis_backend = RedisBackend(
        redis_url,
        compress=config.compress_cache,
        algorithm=config.compression_algorithm,
    )

    if config.cache_backend == "redis":
        return redis_backend

    return HybridBackend(memory_backend, redis_backend)


def _estimate_max_items(size_mb: int, avg_item_size_bytes: int = 1024) -> int:
    if size_mb <= 0:
        return 1024
    total_bytes = size_mb * 1024 * 1024
    return max(1, int(total_bytes / max(1, avg_item_size_bytes)))


__all__ = [
    "build_backend",
    "CacheBackend",
    "HybridBackend",
    "MemoryBackend",
    "RedisBackend",
]
