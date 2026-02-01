"""Admin health endpoints."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ragkit.state.models import ComponentHealth, ComponentStatus

_HOSTED_LLM_PROVIDERS = {"openai", "anthropic", "deepseek", "groq", "mistral"}
_HOSTED_EMBEDDING_PROVIDERS = {"openai", "cohere"}

router = APIRouter(prefix="/health")

_HEALTH_CACHE: dict[str, tuple[float, ComponentHealth]] = {}


class DetailedHealth(BaseModel):
    overall: str
    components: dict
    checked_at: datetime


@router.get("/detailed", response_model=DetailedHealth)
async def get_detailed_health(request: Request) -> DetailedHealth:
    components: dict[str, ComponentHealth] = {}

    vector_store = getattr(request.app.state, "vector_store", None)
    if vector_store is None:
        components["vector_store"] = ComponentHealth(
            name="Vector Store",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Vector store not configured",
        )
    else:
        try:
            start = time.perf_counter()
            await vector_store.count()
            latency = (time.perf_counter() - start) * 1000
            components["vector_store"] = ComponentHealth(
                name="Vector Store",
                status=ComponentStatus.HEALTHY,
                latency_ms=latency,
                last_check=datetime.now(timezone.utc),
                details={"provider": request.app.state.config.vector_store.provider},
            )
        except Exception as exc:  # noqa: BLE001
            components["vector_store"] = ComponentHealth(
                name="Vector Store",
                status=ComponentStatus.UNHEALTHY,
                last_check=datetime.now(timezone.utc),
                message=str(exc),
            )

    components["llm_primary"] = await _check_llm_health(request)
    components["embedding"] = await _check_embedding_health(request)

    if (
        request.app.state.config.retrieval is not None
        and request.app.state.config.retrieval.rerank.enabled
    ):
        components["reranker"] = _check_reranker_health(request)

    statuses = [component.status for component in components.values()]
    if ComponentStatus.UNHEALTHY in statuses:
        overall = ComponentStatus.UNHEALTHY
    elif ComponentStatus.DEGRADED in statuses:
        overall = ComponentStatus.DEGRADED
    elif ComponentStatus.UNKNOWN in statuses:
        overall = ComponentStatus.UNKNOWN
    else:
        overall = ComponentStatus.HEALTHY

    return DetailedHealth(
        overall=overall.value,
        components={name: comp.model_dump() for name, comp in components.items()},
        checked_at=datetime.now(timezone.utc),
    )


async def _check_llm_health(request: Request) -> ComponentHealth:
    if request.app.state.config.llm is None:
        return ComponentHealth(
            name="LLM Primary",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Not configured",
        )
    config = request.app.state.config.llm.primary
    if config.provider in _HOSTED_LLM_PROVIDERS:
        if not (config.api_key or config.api_key_env):
            return ComponentHealth(
                name="LLM Primary",
                status=ComponentStatus.DEGRADED,
                last_check=datetime.now(timezone.utc),
                message="Missing API key",
            )
    health_cfg = request.app.state.config.api.health
    if not health_cfg.active_checks:
        return ComponentHealth(
            name="LLM Primary",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Active health check disabled",
        )

    llm_router = getattr(request.app.state, "llm_router", None)
    if llm_router is None:
        return ComponentHealth(
            name="LLM Primary",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="LLM router not initialized",
        )

    async def _run_check() -> ComponentHealth:
        start = time.perf_counter()
        try:
            await asyncio.wait_for(
                llm_router.primary.complete(
                    [
                        {"role": "system", "content": "Reply with OK."},
                        {"role": "user", "content": "ping"},
                    ]
                ),
                timeout=health_cfg.timeout_seconds,
            )
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="LLM Primary",
                status=ComponentStatus.HEALTHY,
                last_check=datetime.now(timezone.utc),
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return ComponentHealth(
                name="LLM Primary",
                status=ComponentStatus.UNHEALTHY,
                last_check=datetime.now(timezone.utc),
                message=str(exc),
            )

    return await _cached_component("llm_primary", health_cfg.cache_ttl_seconds, _run_check)


async def _check_embedding_health(request: Request) -> ComponentHealth:
    if request.app.state.config.embedding is None:
        return ComponentHealth(
            name="Embedding",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Not configured",
        )
    config = request.app.state.config.embedding.document_model
    if config.provider in _HOSTED_EMBEDDING_PROVIDERS:
        if not (config.api_key or config.api_key_env):
            return ComponentHealth(
                name="Embedding",
                status=ComponentStatus.DEGRADED,
                last_check=datetime.now(timezone.utc),
                message="Missing API key",
            )
    health_cfg = request.app.state.config.api.health
    if not health_cfg.active_checks:
        return ComponentHealth(
            name="Embedding",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Active health check disabled",
        )

    embedder = getattr(request.app.state, "embedder", None)
    if embedder is None:
        return ComponentHealth(
            name="Embedding",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Embedding provider not initialized",
        )

    async def _run_check() -> ComponentHealth:
        start = time.perf_counter()
        try:
            await asyncio.wait_for(
                embedder.embed_query("ping"),
                timeout=health_cfg.timeout_seconds,
            )
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="Embedding",
                status=ComponentStatus.HEALTHY,
                last_check=datetime.now(timezone.utc),
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            return ComponentHealth(
                name="Embedding",
                status=ComponentStatus.UNHEALTHY,
                last_check=datetime.now(timezone.utc),
                message=str(exc),
            )

    return await _cached_component("embedding", health_cfg.cache_ttl_seconds, _run_check)


def _check_reranker_health(request: Request) -> ComponentHealth:
    if request.app.state.config.retrieval is None:
        return ComponentHealth(
            name="Reranker",
            status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Not configured",
        )
    config = request.app.state.config.retrieval.rerank
    if config.provider == "cohere" and not (config.api_key or config.api_key_env):
        return ComponentHealth(
            name="Reranker",
            status=ComponentStatus.DEGRADED,
            last_check=datetime.now(timezone.utc),
            message="Missing API key",
        )
    return ComponentHealth(
        name="Reranker",
        status=ComponentStatus.UNKNOWN,
        last_check=datetime.now(timezone.utc),
        message="Active health check disabled",
    )


async def _cached_component(
    key: str,
    ttl_seconds: int,
    checker: Callable[[], Awaitable[ComponentHealth]],
) -> ComponentHealth:
    if ttl_seconds > 0:
        cached = _HEALTH_CACHE.get(key)
        if cached and (time.monotonic() - cached[0]) < ttl_seconds:
            return cached[1]
    result = await checker()
    _HEALTH_CACHE[key] = (time.monotonic(), result)
    return result
