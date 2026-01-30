"""Admin health endpoints."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ragkit.state.models import ComponentHealth, ComponentStatus

router = APIRouter(prefix="/health")


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

    components["llm_primary"] = _check_llm_health(request)
    components["embedding"] = _check_embedding_health(request)

    if request.app.state.config.retrieval.rerank.enabled:
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


def _check_llm_health(request: Request) -> ComponentHealth:
    config = request.app.state.config.llm.primary
    if config.provider in {"openai", "anthropic"}:
        if not (config.api_key or config.api_key_env):
            return ComponentHealth(
                name="LLM Primary",
                status=ComponentStatus.DEGRADED,
                last_check=datetime.now(timezone.utc),
                message="Missing API key",
            )
    return ComponentHealth(
        name="LLM Primary",
        status=ComponentStatus.UNKNOWN,
        last_check=datetime.now(timezone.utc),
        message="Active health check disabled",
    )


def _check_embedding_health(request: Request) -> ComponentHealth:
    config = request.app.state.config.embedding.document_model
    if config.provider in {"openai", "cohere"}:
        if not (config.api_key or config.api_key_env):
            return ComponentHealth(
                name="Embedding",
                status=ComponentStatus.DEGRADED,
                last_check=datetime.now(timezone.utc),
                message="Missing API key",
            )
    return ComponentHealth(
        name="Embedding",
        status=ComponentStatus.UNKNOWN,
        last_check=datetime.now(timezone.utc),
        message="Active health check disabled",
    )


def _check_reranker_health(request: Request) -> ComponentHealth:
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
