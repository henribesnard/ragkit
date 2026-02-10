"""Dashboard API endpoints for monitoring."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from ragkit.config.schema_v2 import MonitoringConfigV2
from ragkit.monitoring.alerts import AlertManager

router = APIRouter(prefix="/monitoring")


@router.get("/metrics/summary")
async def get_metrics_summary(
    request: Request, time_range: str = Query("24h", pattern="^\\d+[hdm]$")
) -> dict[str, Any]:
    metrics_collector = getattr(request.app.state, "metrics", None)
    if metrics_collector:
        return metrics_collector.get_summary(time_range).model_dump()
    monitoring_collector = getattr(request.app.state, "monitoring_metrics", None)
    if monitoring_collector:
        return monitoring_collector.snapshot()
    return {}


@router.get("/metrics/timeseries")
async def get_metrics_timeseries(
    request: Request,
    metric: str = Query("query_latency_ms"),
    time_range: str = Query("24h", pattern="^\\d+[hdm]$"),
    interval: str = Query("1h", pattern="^\\d+[hdm]$"),
) -> list[dict[str, Any]]:
    metrics_collector = getattr(request.app.state, "metrics", None)
    if not metrics_collector:
        return []
    points = metrics_collector.get_timeseries(metric, time_range, interval)
    return [point.model_dump() for point in points]


@router.get("/alerts")
async def get_alerts(
    request: Request,
    time_range: str = Query("24h", pattern="^\\d+[hdm]$"),
) -> list[dict[str, Any]]:
    config = getattr(request.app.state, "monitoring_config", MonitoringConfigV2())
    alert_manager = AlertManager(config)

    metrics_collector = getattr(request.app.state, "metrics", None)
    summary = metrics_collector.get_summary(time_range) if metrics_collector else None

    monitoring_snapshot = getattr(request.app.state, "monitoring_metrics", None)
    payload: dict[str, Any] = {}
    if summary is not None:
        payload["latency_p95_ms"] = summary.queries.p95_latency_ms

    if monitoring_snapshot is not None:
        snapshot = monitoring_snapshot.snapshot()
        if "faithfulness" in snapshot:
            payload["faithfulness_avg"] = snapshot["faithfulness"]
        if "cost_usd" in snapshot and isinstance(snapshot["cost_usd"], dict):
            payload["cost_daily_usd"] = sum(snapshot["cost_usd"].values())

    alerts = alert_manager.evaluate(summary or payload)
    return [alert.__dict__ for alert in alerts]
