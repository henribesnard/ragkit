"""Cache manager for multi-level caching."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ragkit.cache.embedding_cache import EmbeddingCache
from ragkit.cache.query_cache import QueryCache
from ragkit.cache.result_cache import ResultCache
from ragkit.cache.semantic_matcher import SemanticMatcher
from ragkit.config.schema_v2 import CacheConfigV2

ComputeFn = Callable[..., Awaitable[Any]]
EmbedFn = Callable[[str], Awaitable[list[float]]]
RetrieveFn = Callable[[list[float]], Awaitable[Any]]
BatchEmbedFn = Callable[
    [list[str]],
    Awaitable[list[list[float]]] | list[list[float]],
]


@dataclass
class CacheMetrics:
    hits: dict[str, int] = field(default_factory=dict)
    misses: dict[str, int] = field(default_factory=dict)
    latency_saved_ms: dict[str, float] = field(default_factory=dict)
    cost_saved_usd: dict[str, float] = field(default_factory=dict)

    def record_hit(
        self,
        cache_name: str,
        latency_saved_ms: float = 0.0,
        cost_saved_usd: float = 0.0,
    ) -> None:
        self.hits[cache_name] = self.hits.get(cache_name, 0) + 1
        if latency_saved_ms:
            self.latency_saved_ms[cache_name] = (
                self.latency_saved_ms.get(cache_name, 0.0) + latency_saved_ms
            )
        if cost_saved_usd:
            self.cost_saved_usd[cache_name] = (
                self.cost_saved_usd.get(cache_name, 0.0) + cost_saved_usd
            )

    def record_miss(self, cache_name: str) -> None:
        self.misses[cache_name] = self.misses.get(cache_name, 0) + 1

    def hit_rate(self, cache_name: str) -> float:
        hits = self.hits.get(cache_name, 0)
        misses = self.misses.get(cache_name, 0)
        total = hits + misses
        return hits / total if total else 0.0

    def latency_saved_total_ms(self) -> float:
        return sum(self.latency_saved_ms.values())

    def cost_saved_total_usd(self) -> float:
        return sum(self.cost_saved_usd.values())


class CacheManager:
    """Orchestrate query, embedding, and result caches."""

    def __init__(
        self,
        config: CacheConfigV2,
        embedder: BatchEmbedFn | None = None,
    ) -> None:
        self.config = config
        self.metrics = CacheMetrics()
        self.semantic_matcher: SemanticMatcher | None
        if embedder and config.cache_key_strategy == "semantic":
            self.semantic_matcher = SemanticMatcher(config, embedder=embedder)
        else:
            self.semantic_matcher = None
        self.query_cache = (
            QueryCache(config, semantic_matcher=self.semantic_matcher)
            if config.query_cache_enabled
            else None
        )
        self.embedding_cache = EmbeddingCache(config) if config.embedding_cache_enabled else None
        self.result_cache = ResultCache(config) if config.result_cache_enabled else None

    async def get_or_compute(
        self,
        query: str,
        compute_fn: ComputeFn,
        embed_fn: EmbedFn | None = None,
        retrieve_fn: RetrieveFn | None = None,
        latency_estimates: dict[str, float] | None = None,
        cost_estimates: dict[str, float] | None = None,
    ) -> Any:
        """Resolve query through cache layers or compute."""
        if self.query_cache:
            cached = await self.query_cache.get(query)
            if cached is not None:
                self.metrics.record_hit(
                    "query_cache",
                    latency_saved_ms=_estimate(latency_estimates, "query_cache"),
                    cost_saved_usd=_estimate(cost_estimates, "query_cache"),
                )
                return cached
            self.metrics.record_miss("query_cache")

        embedding: list[float] | None = None
        if embed_fn:
            embedding = await self._get_embedding(
                query,
                embed_fn,
                latency_estimates=latency_estimates,
                cost_estimates=cost_estimates,
            )

        result = None
        if retrieve_fn and embedding is not None and self.result_cache:
            result = await self.result_cache.get(embedding)
            if result is not None:
                self.metrics.record_hit(
                    "result_cache",
                    latency_saved_ms=_estimate(latency_estimates, "result_cache"),
                    cost_saved_usd=_estimate(cost_estimates, "result_cache"),
                )
            else:
                self.metrics.record_miss("result_cache")
                result = await retrieve_fn(embedding)
                await self.result_cache.set(embedding, result)

        response = await _call_with_available_args(
            compute_fn,
            query=query,
            embedding=embedding,
            result=result,
        )

        if self.query_cache:
            await self.query_cache.set(query, response)
        return response

    async def _get_embedding(
        self,
        query: str,
        embed_fn: EmbedFn,
        latency_estimates: dict[str, float] | None = None,
        cost_estimates: dict[str, float] | None = None,
    ) -> list[float]:
        if self.embedding_cache:
            cached = await self.embedding_cache.get(query)
            if cached is not None:
                self.metrics.record_hit(
                    "embedding_cache",
                    latency_saved_ms=_estimate(latency_estimates, "embedding_cache"),
                    cost_saved_usd=_estimate(cost_estimates, "embedding_cache"),
                )
                return cached
            self.metrics.record_miss("embedding_cache")

        embedding = await embed_fn(query)
        if self.embedding_cache:
            await self.embedding_cache.set(query, embedding)
        return embedding


async def _call_with_available_args(func: ComputeFn, **kwargs: Any) -> Any:
    signature = inspect.signature(func)
    accepted = {name: value for name, value in kwargs.items() if name in signature.parameters}
    return await func(**accepted)


def _estimate(estimates: dict[str, float] | None, key: str) -> float:
    if not estimates:
        return 0.0
    return float(estimates.get(key, 0.0))
