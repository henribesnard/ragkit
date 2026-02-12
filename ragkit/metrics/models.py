"""Metrics models for RAGKIT."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class MetricPoint(BaseModel):
    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class QueryMetrics(BaseModel):
    total: int = 0
    success: int = 0
    failed: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    by_intent: dict[str, int] = Field(default_factory=dict)


class IngestionMetrics(BaseModel):
    total_runs: int = 0
    total_documents: int = 0
    total_chunks: int = 0
    avg_duration_seconds: float = 0.0
    last_run: datetime | None = None
    errors: int = 0


class ComponentMetrics(BaseModel):
    name: str
    calls: int = 0
    errors: int = 0
    avg_latency_ms: float = 0.0
    last_error: str | None = None


class MetricsSummary(BaseModel):
    period: str
    queries: QueryMetrics
    ingestion: IngestionMetrics
    components: dict[str, ComponentMetrics]
    generated_at: datetime
