"""Tests for admin API endpoints (config, metrics, health, ingestion)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ragkit.api.app import create_app
from ragkit.config import ConfigLoader
from ragkit.metrics.collector import MetricsCollector
from ragkit.state.store import StateStore
from tests.helpers import DummyOrchestrator


@pytest.fixture(autouse=True)
def reset_metrics_singleton():
    MetricsCollector._instance = None
    if hasattr(MetricsCollector, "_initialized"):
        delattr(MetricsCollector, "_initialized")
    yield
    MetricsCollector._instance = None
    if hasattr(MetricsCollector, "_initialized"):
        delattr(MetricsCollector, "_initialized")


def _make_app(tmp_path: Path):
    loader = ConfigLoader()
    config = loader.load(Path("ragkit-v1-config.yaml"))

    state_store = StateStore(db_path=tmp_path / "state.db")
    metrics = MetricsCollector(db_path=tmp_path / "metrics.db")

    return create_app(
        config,
        DummyOrchestrator(),
        config_path=tmp_path / "ragkit.yaml",
        state_store=state_store,
        metrics=metrics,
    )


# ---------- Config endpoints ----------


def test_get_config(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/config")
    assert response.status_code == 200
    data = response.json()
    assert "config" in data
    assert "loaded_at" in data


def test_validate_config_valid(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    loader = ConfigLoader()
    config = loader.load(Path("ragkit-v1-config.yaml"))

    response = client.post(
        "/api/v1/admin/config/validate",
        json={"config": config.model_dump(), "validate_only": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data


def test_validate_config_invalid(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/v1/admin/config/validate",
        json={"config": {"bad": "config"}, "validate_only": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


def test_export_config(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/config/export")
    assert response.status_code == 200
    assert "yaml" in response.headers.get("content-type", "")


# ---------- Metrics endpoints ----------


def test_get_metrics_summary(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "queries" in data


def test_get_query_logs_empty(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/metrics/queries")
    assert response.status_code == 200
    assert response.json() == []


def test_get_timeseries(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/metrics/timeseries/query_count")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------- Health endpoints ----------


def test_detailed_health(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "components" in data
    assert "checked_at" in data


# ---------- Ingestion endpoints ----------


def test_ingestion_status(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/ingestion/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert "total_documents" in data


def test_ingestion_history_empty(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/ingestion/history")
    assert response.status_code == 200
    assert response.json() == []


def test_ingestion_job_not_found(tmp_path):
    app = _make_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/ingestion/jobs/nonexistent")
    assert response.status_code == 404
