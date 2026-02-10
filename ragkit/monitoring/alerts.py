"""Alerting utilities for monitoring thresholds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ragkit.config.schema_v2 import MonitoringConfigV2
from ragkit.metrics.models import MetricsSummary


@dataclass
class Alert:
    name: str
    severity: str
    message: str
    value: float
    threshold: float
    timestamp: datetime


class AlertManager:
    """Evaluate metrics against thresholds and emit alerts."""

    def __init__(self, config: MonitoringConfigV2) -> None:
        self.config = config

    def evaluate(self, metrics: MetricsSummary | dict[str, Any] | None) -> list[Alert]:
        if not self.config.enable_alerts or metrics is None:
            return []

        normalized = _normalize_metrics(metrics)
        alerts: list[Alert] = []
        now = datetime.now(timezone.utc)

        latency_p95 = normalized.get("latency_p95_ms")
        if latency_p95 is not None and latency_p95 > self.config.alert_latency_p95_threshold_ms:
            alerts.append(
                Alert(
                    name="latency_p95_ms",
                    severity="warning",
                    message=(
                        f"Latency p95 {latency_p95:.0f}ms exceeds "
                        f"threshold {self.config.alert_latency_p95_threshold_ms}ms"
                    ),
                    value=float(latency_p95),
                    threshold=float(self.config.alert_latency_p95_threshold_ms),
                    timestamp=now,
                )
            )

        faithfulness = normalized.get("faithfulness_avg")
        if (
            faithfulness is not None
            and faithfulness < self.config.alert_faithfulness_threshold
        ):
            alerts.append(
                Alert(
                    name="faithfulness_avg",
                    severity="warning",
                    message=(
                        f"Faithfulness {faithfulness:.2f} below "
                        f"threshold {self.config.alert_faithfulness_threshold:.2f}"
                    ),
                    value=float(faithfulness),
                    threshold=float(self.config.alert_faithfulness_threshold),
                    timestamp=now,
                )
            )

        cost_daily = normalized.get("cost_daily_usd")
        if cost_daily is not None and cost_daily > self.config.alert_cost_daily_threshold_usd:
            alerts.append(
                Alert(
                    name="cost_daily_usd",
                    severity="warning",
                    message=(
                        f"Daily cost ${cost_daily:.2f} exceeds "
                        f"threshold ${self.config.alert_cost_daily_threshold_usd:.2f}"
                    ),
                    value=float(cost_daily),
                    threshold=float(self.config.alert_cost_daily_threshold_usd),
                    timestamp=now,
                )
            )

        return alerts


def _normalize_metrics(metrics: MetricsSummary | dict[str, Any]) -> dict[str, float]:
    if isinstance(metrics, MetricsSummary):
        return {
            "latency_p95_ms": metrics.queries.p95_latency_ms,
            "latency_p99_ms": metrics.queries.p99_latency_ms,
        }

    normalized: dict[str, float] = {}
    for key in ("latency_p95_ms", "latency_p99_ms", "faithfulness_avg", "cost_daily_usd"):
        value = metrics.get(key)
        if value is not None:
            normalized[key] = float(value)
    return normalized
