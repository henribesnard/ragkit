"""Tests for ragkit.state.store."""

from datetime import datetime, timezone

import pytest

from ragkit.state.store import StateStore


@pytest.fixture
def store(tmp_path):
    return StateStore(db_path=tmp_path / "test_state.db")


def test_get_default(store):
    assert store.get("missing_key") is None
    assert store.get("missing_key", "fallback") == "fallback"


def test_set_and_get_string(store):
    store.set("greeting", "hello")
    assert store.get("greeting") == "hello"


def test_set_and_get_dict(store):
    store.set("config", {"key": "value", "num": 42})
    result = store.get("config")
    assert result == {"key": "value", "num": 42}


def test_set_and_get_list(store):
    store.set("items", [1, 2, 3])
    assert store.get("items") == [1, 2, 3]


def test_overwrite(store):
    store.set("key", "old")
    store.set("key", "new")
    assert store.get("key") == "new"


def test_add_ingestion_run(store):
    run_id = store.add_ingestion_run(
        stats={"documents_loaded": 10, "chunks_stored": 50},
        status="completed",
    )
    assert isinstance(run_id, int)
    assert run_id > 0


def test_ingestion_history(store):
    store.add_ingestion_run(stats={"docs": 5}, status="completed")
    store.add_ingestion_run(stats={"docs": 3}, status="failed")
    store.add_ingestion_run(stats=None, status="running")

    history = store.get_ingestion_history(limit=10)
    assert len(history) == 3
    # Most recent first
    assert history[0]["status"] == "running"
    assert history[1]["status"] == "failed"
    assert history[2]["status"] == "completed"


def test_ingestion_history_limit(store):
    for i in range(5):
        store.add_ingestion_run(stats={"i": i}, status="completed")

    history = store.get_ingestion_history(limit=2)
    assert len(history) == 2


def test_ingestion_run_with_timestamps(store):
    started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    completed = datetime(2025, 1, 1, 12, 5, 0, tzinfo=timezone.utc)

    store.add_ingestion_run(
        stats={"docs": 10},
        status="completed",
        started_at=started,
        completed_at=completed,
    )

    history = store.get_ingestion_history(limit=1)
    assert history[0]["started_at"] == started.isoformat()
    assert history[0]["completed_at"] == completed.isoformat()
