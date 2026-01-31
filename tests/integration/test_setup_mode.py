"""Integration tests for setup mode."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ragkit.api.app import create_app
from ragkit.config import ConfigLoader
from ragkit.config.schema import ProjectConfig, RAGKitConfig
from tests.helpers import DummyOrchestrator


def _make_setup_app(tmp_path: Path):
    cfg = RAGKitConfig(version="1.0", project=ProjectConfig(name="test"))
    return create_app(cfg, config_path=tmp_path / "ragkit.yaml", setup_mode=True)


def _make_normal_app(tmp_path: Path):
    loader = ConfigLoader()
    config = loader.load(Path("ragkit-v1-config.yaml"))
    return create_app(
        config,
        DummyOrchestrator(),
        config_path=tmp_path / "ragkit.yaml",
        setup_mode=False,
    )


def test_status_endpoint_setup_mode(tmp_path):
    app = _make_setup_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["setup_mode"] is True


def test_status_endpoint_normal_mode(tmp_path):
    app = _make_normal_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert data["setup_mode"] is False


def test_query_blocked_in_setup_mode(tmp_path):
    app = _make_setup_app(tmp_path)
    client = TestClient(app)

    response = client.post("/api/v1/query", json={"query": "test"})
    assert response.status_code == 503


def test_ingestion_run_blocked_in_setup_mode(tmp_path):
    app = _make_setup_app(tmp_path)
    client = TestClient(app)

    response = client.post("/api/v1/admin/ingestion/run", json={"incremental": True})
    assert response.status_code == 503


def test_config_accessible_in_setup_mode(tmp_path):
    app = _make_setup_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/config")
    assert response.status_code == 200


def test_health_accessible_in_setup_mode(tmp_path):
    app = _make_setup_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/health/detailed")
    assert response.status_code == 200


def test_ingestion_status_accessible_in_setup_mode(tmp_path):
    app = _make_setup_app(tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/admin/ingestion/status")
    assert response.status_code == 200
