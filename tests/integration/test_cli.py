"""Tests for ragkit CLI commands."""

from __future__ import annotations

from pathlib import Path
import types

import pytest
from typer.testing import CliRunner

from ragkit.cli import main as cli
from tests.helpers import DummyEmbedder, DummyVectorStore

runner = CliRunner()


class DummyConfigLoader:
    def __init__(self, config):
        self._config = config

    def load_with_env(self, path: Path):
        return self._config


class DummyPipeline:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def run(self, incremental: bool = False):
        return types.SimpleNamespace(status="ok")


class DummyOrchestrator:
    def __init__(self, *args, **kwargs):
        pass

    async def process(self, query, history=None):
        response = types.SimpleNamespace(content="ok")
        return types.SimpleNamespace(response=response)


def _stub_config():
    return types.SimpleNamespace(
        ingestion=types.SimpleNamespace(),
        embedding=types.SimpleNamespace(document_model=types.SimpleNamespace(), query_model=types.SimpleNamespace()),
        vector_store=types.SimpleNamespace(),
        retrieval=types.SimpleNamespace(),
        llm=types.SimpleNamespace(),
        agents=types.SimpleNamespace(),
        api=types.SimpleNamespace(
            server=types.SimpleNamespace(host="0.0.0.0", port=8000),
            docs=types.SimpleNamespace(enabled=True, path="/docs"),
            cors=types.SimpleNamespace(enabled=True, origins=["*"]),
            streaming=types.SimpleNamespace(enabled=False),
            enabled=True,
        ),
        chatbot=types.SimpleNamespace(
            server=types.SimpleNamespace(host="0.0.0.0", port=8080, share=False),
            ui=types.SimpleNamespace(theme="soft", title="RAGKIT", description="", placeholder="", examples=[]),
            features=types.SimpleNamespace(streaming=False, show_sources=True, show_latency=True),
        ),
        observability=types.SimpleNamespace(metrics=types.SimpleNamespace(enabled=True)),
    )


def test_init_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli.app, ["init", "my-project", "--template", "minimal"])
    assert result.exit_code == 0
    assert (tmp_path / "my-project" / "ragkit.yaml").exists()
    assert (tmp_path / "my-project" / "data" / "documents").exists()


def test_init_fails_if_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "existing").mkdir()
    result = runner.invoke(cli.app, ["init", "existing"])
    assert result.exit_code != 0


def test_validate_valid_config(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "test")
    monkeypatch.setenv("COHERE_API_KEY", "test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    result = runner.invoke(cli.app, ["validate", "-c", "ragkit-v1-config.yaml"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_validate_invalid_config(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("invalid: [yaml")
    result = runner.invoke(cli.app, ["validate", "-c", str(bad)])
    assert result.exit_code != 0


def test_ingest_runs_pipeline(monkeypatch):
    dummy_config = _stub_config()
    monkeypatch.setattr(cli, "ConfigLoader", lambda: DummyConfigLoader(dummy_config))
    monkeypatch.setattr(cli, "create_embedder", lambda *_: DummyEmbedder())
    monkeypatch.setattr(cli, "create_vector_store", lambda *_: DummyVectorStore())
    monkeypatch.setattr(cli, "IngestionPipeline", DummyPipeline)

    result = runner.invoke(cli.app, ["ingest", "-c", "dummy.yaml"])
    assert result.exit_code == 0


def test_query_outputs_response(monkeypatch):
    dummy_config = _stub_config()
    monkeypatch.setattr(cli, "ConfigLoader", lambda: DummyConfigLoader(dummy_config))
    monkeypatch.setattr(cli, "create_embedder", lambda *_: DummyEmbedder())
    monkeypatch.setattr(cli, "create_vector_store", lambda *_: DummyVectorStore())
    monkeypatch.setattr(cli, "RetrievalEngine", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli, "LLMRouter", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli, "AgentOrchestrator", DummyOrchestrator)

    result = runner.invoke(cli.app, ["query", "hello", "-c", "dummy.yaml"])
    assert result.exit_code == 0
    assert "ok" in result.stdout


def test_serve_creates_app(monkeypatch):
    import uvicorn
    import ragkit.api.app as api_app

    dummy_config = _stub_config()
    monkeypatch.setattr(cli, "ConfigLoader", lambda: DummyConfigLoader(dummy_config))
    monkeypatch.setattr(cli, "create_embedder", lambda *_: DummyEmbedder())
    monkeypatch.setattr(cli, "create_vector_store", lambda *_: DummyVectorStore())
    monkeypatch.setattr(cli, "RetrievalEngine", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli, "LLMRouter", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli, "AgentOrchestrator", DummyOrchestrator)
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(api_app, "create_app", lambda *args, **kwargs: object())

    result = runner.invoke(cli.app, ["serve", "--api-only", "-c", "dummy.yaml"])
    assert result.exit_code == 0


def test_ui_build_missing_directory(tmp_path, monkeypatch):
    fake_root = tmp_path / "ragkit" / "cli"
    fake_root.mkdir(parents=True)
    monkeypatch.setattr(cli, "__file__", str(fake_root / "main.py"))

    result = runner.invoke(cli.app, ["ui", "build"])
    assert result.exit_code != 0
    assert "ragkit-ui" in result.stdout


def test_ui_dev_missing_directory(tmp_path, monkeypatch):
    fake_root = tmp_path / "ragkit" / "cli"
    fake_root.mkdir(parents=True)
    monkeypatch.setattr(cli, "__file__", str(fake_root / "main.py"))

    result = runner.invoke(cli.app, ["ui", "dev"])
    assert result.exit_code != 0
    assert "ragkit-ui" in result.stdout
