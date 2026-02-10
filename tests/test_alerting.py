"""Tests for alerting thresholds."""

from datetime import datetime, timezone

from ragkit.config.schema_v2 import MonitoringConfigV2
from ragkit.metrics.models import IngestionMetrics, MetricsSummary, QueryMetrics
from ragkit.monitoring.alerts import AlertManager


def test_latency_alert_triggers():
    config = MonitoringConfigV2(alert_latency_p95_threshold_ms=1000)
    manager = AlertManager(config)
    summary = MetricsSummary(
        period="24h",
        queries=QueryMetrics(p95_latency_ms=1500),
        ingestion=IngestionMetrics(),
        components={},
        generated_at=datetime.now(timezone.utc),
    )
    alerts = manager.evaluate(summary)
    assert any(alert.name == "latency_p95_ms" for alert in alerts)


def test_faithfulness_alert_triggers():
    config = MonitoringConfigV2(alert_faithfulness_threshold=0.8)
    manager = AlertManager(config)
    alerts = manager.evaluate({"faithfulness_avg": 0.5})
    assert any(alert.name == "faithfulness_avg" for alert in alerts)


def test_cost_alert_triggers():
    config = MonitoringConfigV2(alert_cost_daily_threshold_usd=10.0)
    manager = AlertManager(config)
    alerts = manager.evaluate({"cost_daily_usd": 20.0})
    assert any(alert.name == "cost_daily_usd" for alert in alerts)


def test_alerts_disabled():
    config = MonitoringConfigV2(enable_alerts=False)
    manager = AlertManager(config)
    alerts = manager.evaluate({"latency_p95_ms": 9999})
    assert alerts == []
