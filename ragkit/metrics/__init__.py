"""Metrics collection entrypoints."""

from ragkit.metrics.collector import MetricsCollector
from ragkit.metrics.models import (
    ComponentMetrics,
    IngestionMetrics,
    MetricPoint,
    MetricType,
    MetricsSummary,
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
