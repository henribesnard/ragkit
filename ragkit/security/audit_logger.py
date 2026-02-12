"""Audit logging for security and compliance."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ragkit.config.schema_v2 import SecurityConfigV2
from ragkit.security.exceptions import AuditLogError

DEFAULT_AUDIT_DB_PATH = Path.home() / ".ragkit" / "audit_logs.db"


@dataclass(frozen=True)
class AuditLogEntry:
    timestamp: datetime
    user_id: str | None
    query_hash: str
    query_text: str | None
    query_length: int
    response_length: int
    documents_accessed: list[str]
    latency_ms: float | None
    cost_usd: float | None
    pii_detected: list[str]
    toxicity_score: float | None
    metadata: dict[str, Any]


class AuditLogger:
    """Store security-relevant audit logs in SQLite."""

    def __init__(self, config: SecurityConfigV2, db_path: Path | str | None = None) -> None:
        self.config = config
        self.db_path = Path(db_path) if db_path else DEFAULT_AUDIT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def log_query(
        self,
        user_id: str | None,
        query: str,
        response: str,
        documents_accessed: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        pii_detected: list[str] | None = None,
        toxicity_score: float | None = None,
    ) -> None:
        if not self.config.audit_logging_enabled:
            return

        now = datetime.now(timezone.utc)
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        query_text = query if self.config.log_all_queries else None

        entry = AuditLogEntry(
            timestamp=now,
            user_id=user_id,
            query_hash=query_hash,
            query_text=query_text,
            query_length=len(query),
            response_length=len(response),
            documents_accessed=documents_accessed or [],
            latency_ms=_get_float(metadata, "latency_ms"),
            cost_usd=_get_float(metadata, "cost_usd"),
            pii_detected=pii_detected or [],
            toxicity_score=toxicity_score,
            metadata=metadata or {},
        )

        try:
            self._insert_entry(entry)
            if self.config.log_retention_days > 0:
                cutoff = now - timedelta(days=self.config.log_retention_days)
                self.purge_before(cutoff)
        except Exception as exc:
            raise AuditLogError(str(exc)) from exc

    def list_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def purge_before(self, cutoff: datetime) -> int:
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM audit_logs WHERE timestamp < ?",
                (cutoff.isoformat(),),
            )
            return cursor.rowcount

    def _ensure_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    query_hash TEXT NOT NULL,
                    query_text TEXT,
                    query_length INTEGER,
                    response_length INTEGER,
                    documents_accessed TEXT,
                    latency_ms REAL,
                    cost_usd REAL,
                    pii_detected TEXT,
                    toxicity_score REAL,
                    metadata_json TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)")

    def _insert_entry(self, entry: AuditLogEntry) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    id,
                    timestamp,
                    user_id,
                    query_hash,
                    query_text,
                    query_length,
                    response_length,
                    documents_accessed,
                    latency_ms,
                    cost_usd,
                    pii_detected,
                    toxicity_score,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    entry.timestamp.isoformat(),
                    entry.user_id,
                    entry.query_hash,
                    entry.query_text,
                    entry.query_length,
                    entry.response_length,
                    json.dumps(entry.documents_accessed),
                    entry.latency_ms,
                    entry.cost_usd,
                    json.dumps(entry.pii_detected),
                    entry.toxicity_score,
                    json.dumps(entry.metadata),
                ),
            )

    @contextmanager
    def _connection(self) -> Any:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _get_float(metadata: dict[str, Any] | None, key: str) -> float | None:
    if not metadata:
        return None
    value = metadata.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
