"""Persistent state storage using SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path(".ragkit") / "state.db"
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ingestion_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    stats TEXT,
                    status TEXT NOT NULL
                );
                """
            )

    def get(self, key: str, default: Any = None) -> Any:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            return default

    def set(self, key: str, value: Any) -> None:
        payload = json.dumps(_serialize(value))
        updated_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO state (key, value, updated_at) VALUES (?, ?, ?)",
                (key, payload, updated_at),
            )

    def get_ingestion_history(self, limit: int = 10) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, started_at, completed_at, stats, status
                FROM ingestion_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        history: list[dict] = []
        for row in rows:
            stats = None
            if row[3]:
                try:
                    stats = json.loads(row[3])
                except json.JSONDecodeError:
                    stats = None
            history.append(
                {
                    "id": row[0],
                    "started_at": row[1],
                    "completed_at": row[2],
                    "stats": stats,
                    "status": row[4],
                }
            )
        return history

    def add_ingestion_run(
        self,
        stats: dict | None,
        status: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> int:
        started_at = started_at or datetime.now(timezone.utc)
        stats_payload = json.dumps(_serialize(stats)) if stats is not None else None
        completed_payload = completed_at.isoformat() if completed_at else None
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO ingestion_history (started_at, completed_at, stats, status)
                VALUES (?, ?, ?, ?)
                """,
                (started_at.isoformat(), completed_payload, stats_payload, status),
            )
            return int(cursor.lastrowid)


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _serialize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value
