"""Admin metrics endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

_METRIC_ALIASES = {
    "query_latency": "query_latency_ms",
    "component_latency": "component_latency_ms",
    "ingestion_count": "ingestion_runs",
    "ingestion_duration": "ingestion_duration_seconds",
}

router = APIRouter(prefix="/metrics")


@router.get("/summary")
async def get_metrics_summary(
    request: Request, period: str = Query("24h", pattern="^\\d+[hdm]$")
) -> dict[str, Any]:
    metrics_collector = getattr(request.app.state, "metrics", None)
    if not metrics_collector:
        return {}
    return metrics_collector.get_summary(period).model_dump()


@router.get("/timeseries/{metric}")
async def get_metric_timeseries(
    request: Request,
    metric: str,
    period: str = Query("24h"),
    interval: str = Query("1h"),
) -> list[Any]:
    metrics_collector = getattr(request.app.state, "metrics", None)
    metric_name = _METRIC_ALIASES.get(metric, metric)
    return (
        metrics_collector.get_timeseries(metric_name, period, interval) if metrics_collector else []
    )


@router.get("/queries")
async def get_query_logs(
    request: Request,
    limit: int = Query(100, le=1000),
    offset: int = 0,
) -> list[dict[str, Any]]:
    metrics_collector = getattr(request.app.state, "metrics", None)
    return metrics_collector.get_query_logs(limit, offset) if metrics_collector else []
