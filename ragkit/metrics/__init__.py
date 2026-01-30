"""Metrics collection entrypoints."""

from ragkit.metrics.collector import MetricsCollector
from ragkit.metrics.models import (
    ComponentMetrics,
    IngestionMetrics,
    MetricPoint,
    MetricsSummary,
    MetricType,
    QueryMetrics,
)

metrics = MetricsCollector()

__all__ = [
    "ComponentMetrics",
    "IngestionMetrics",
    "MetricPoint",
    "MetricType",
    "MetricsSummary",
    "MetricsCollector",
    "QueryMetrics",
    "metrics",
]
