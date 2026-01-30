"""Tests for ragkit.metrics.collector."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ragkit.metrics.collector import MetricsCollector


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset MetricsCollector singleton between tests."""
    MetricsCollector._instance = None
    if hasattr(MetricsCollector, "_initialized"):
        delattr(MetricsCollector, "_initialized")
    yield
    MetricsCollector._instance = None
    if hasattr(MetricsCollector, "_initialized"):
        delattr(MetricsCollector, "_initialized")


@pytest.fixture
def collector(tmp_path):
    return MetricsCollector(db_path=tmp_path / "test_metrics.db")


def test_record_and_get_query_logs(collector):
    collector.record_query("What is Python?", latency_ms=120.5, success=True, intent="question")
    collector.record_query("Fail query", latency_ms=50.0, success=False, error="timeout")

    logs = collector.get_query_logs(limit=10)
    assert len(logs) == 2
    # Most recent first
    assert logs[0]["query"] == "Fail query"
    assert logs[0]["success"] is False
    assert logs[0]["error"] == "timeout"
    assert logs[1]["query"] == "What is Python?"
    assert logs[1]["success"] is True
    assert logs[1]["intent"] == "question"


def test_query_logs_pagination(collector):
    for i in range(5):
        collector.record_query(f"query_{i}", latency_ms=10.0, success=True)

    page1 = collector.get_query_logs(limit=2, offset=0)
    page2 = collector.get_query_logs(limit=2, offset=2)

    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0]["query"] != page2[0]["query"]


def test_get_summary(collector):
    collector.record_query("q1", latency_ms=100.0, success=True, intent="question")
    collector.record_query("q2", latency_ms=200.0, success=False, intent="question")

    summary = collector.get_summary("24h")
    assert summary.period == "24h"
    assert summary.queries.total == 2
    assert summary.queries.success == 1
    assert summary.queries.failed == 1
    assert summary.queries.avg_latency_ms == 150.0


def test_record_ingestion(collector):
    stats = SimpleNamespace(
        documents_loaded=10,
        chunks_stored=50,
        duration_seconds=3.5,
        errors=0,
    )
    collector.record_ingestion(stats)

    summary = collector.get_summary("24h")
    assert summary.ingestion.total_runs == 1
    assert summary.ingestion.total_documents == 10
    assert summary.ingestion.total_chunks == 50


def test_record_component_call(collector):
    collector.record_component_call("embedder", latency_ms=45.0, success=True)
    collector.record_component_call("embedder", latency_ms=55.0, success=False, error="timeout")

    summary = collector.get_summary("24h")
    assert "embedder" in summary.components
    assert summary.components["embedder"].calls == 2
    assert summary.components["embedder"].errors == 1


def test_timeseries(collector):
    collector.record_query("q1", latency_ms=100.0, success=True)
    collector.record_query("q2", latency_ms=200.0, success=True)

    ts = collector.get_timeseries("query_count", "24h", "1h")
    assert len(ts) >= 1
    total_value = sum(p.value for p in ts)
    assert total_value == 2


def test_empty_summary(collector):
    summary = collector.get_summary("24h")
    assert summary.queries.total == 0
    assert summary.ingestion.total_runs == 0
    assert summary.components == {}
