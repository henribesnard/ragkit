"""Admin metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/metrics")


@router.get("/summary")
async def get_metrics_summary(request: Request, period: str = Query("24h", pattern="^\\d+[hdm]$")):
    metrics_collector = getattr(request.app.state, "metrics", None)
    return metrics_collector.get_summary(period) if metrics_collector else {}


@router.get("/timeseries/{metric}")
async def get_metric_timeseries(
    request: Request,
    metric: str,
    period: str = Query("24h"),
    interval: str = Query("1h"),
):
    metrics_collector = getattr(request.app.state, "metrics", None)
    return metrics_collector.get_timeseries(metric, period, interval) if metrics_collector else []


@router.get("/queries")
async def get_query_logs(
    request: Request,
    limit: int = Query(100, le=1000),
    offset: int = 0,
):
    metrics_collector = getattr(request.app.state, "metrics", None)
    return metrics_collector.get_query_logs(limit, offset) if metrics_collector else []
