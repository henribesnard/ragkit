"""Metrics collection and aggregation."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ragkit.metrics.models import (
    ComponentMetrics,
    IngestionMetrics,
    MetricPoint,
    MetricsSummary,
    QueryMetrics,
)


class MetricsCollector:
    """Collects and stores metrics for RAGKIT operations."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or Path(".ragkit") / "metrics.db"
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    labels TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_metrics_name_ts
                ON metrics(name, timestamp);

                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    intent TEXT,
                    latency_ms REAL NOT NULL,
                    success INTEGER NOT NULL,
                    error TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS component_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    success INTEGER NOT NULL,
                    error TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ingestion_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documents_loaded INTEGER NOT NULL,
                    chunks_stored INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    errors INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                );
                """
            )

    def record_query(
        self,
        query: str,
        latency_ms: float,
        success: bool,
        intent: str | None = None,
        error: str | None = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO query_logs (query, intent, latency_ms, success, error, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    query,
                    intent,
                    float(latency_ms),
                    1 if success else 0,
                    error,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self._record_metric(conn, "query_count", 1, {"success": str(success)})
            self._record_metric(conn, "query_latency_ms", float(latency_ms))

    def record_component_call(
        self,
        component: str,
        latency_ms: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO component_logs (component, latency_ms, success, error, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    component,
                    float(latency_ms),
                    1 if success else 0,
                    error,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self._record_metric(
                conn, "component_latency_ms", float(latency_ms), {"component": component}
            )
            if not success:
                self._record_metric(conn, "component_error", 1, {"component": component})

    def record_ingestion(self, stats: Any) -> None:
        documents = int(getattr(stats, "documents_loaded", 0))
        chunks = int(getattr(stats, "chunks_stored", 0))
        duration = float(getattr(stats, "duration_seconds", 0.0))
        errors = int(getattr(stats, "errors", 0))

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ingestion_logs (
                    documents_loaded,
                    chunks_stored,
                    duration_seconds,
                    errors,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (documents, chunks, duration, errors, datetime.now(timezone.utc).isoformat()),
            )
            self._record_metric(conn, "ingestion_runs", 1)
            self._record_metric(conn, "ingestion_documents", documents)
            self._record_metric(conn, "ingestion_chunks", chunks)
            self._record_metric(conn, "ingestion_duration_seconds", duration)
            if errors:
                self._record_metric(conn, "ingestion_errors", errors)

    def get_summary(self, period: str) -> MetricsSummary:
        start = _period_start(period)
        queries = self._query_metrics(start)
        ingestion = self._ingestion_metrics(start)
        components = self._component_metrics(start)
        return MetricsSummary(
            period=period,
            queries=queries,
            ingestion=ingestion,
            components=components,
            generated_at=datetime.now(timezone.utc),
        )

    def get_timeseries(self, metric: str, period: str, interval: str = "1h") -> list[MetricPoint]:
        start = _period_start(period)
        interval_delta = _parse_interval(interval)
        rows = self._fetch_metric_rows(metric, start)
        buckets: dict[datetime, float] = {}
        for ts, value in rows:
            bucket = _floor_time(ts, interval_delta)
            buckets[bucket] = buckets.get(bucket, 0.0) + float(value)
        return [
            MetricPoint(timestamp=bucket, value=value)
            for bucket, value in sorted(buckets.items(), key=lambda item: item[0])
        ]

    def get_query_logs(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT query, intent, latency_ms, success, error, timestamp
                FROM query_logs
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [
            {
                "query": row[0],
                "intent": row[1],
                "latency_ms": row[2],
                "success": bool(row[3]),
                "error": row[4],
                "timestamp": row[5],
            }
            for row in rows
        ]

    def _record_metric(
        self,
        conn: sqlite3.Connection,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        conn.execute(
            "INSERT INTO metrics (name, value, labels, timestamp) VALUES (?, ?, ?, ?)",
            (
                name,
                float(value),
                json.dumps(labels or {}),
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def _fetch_metric_rows(self, name: str, start: datetime) -> list[tuple[datetime, float]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT timestamp, value FROM metrics WHERE name = ? AND timestamp >= ?",
                (name, start.isoformat()),
            ).fetchall()
        parsed: list[tuple[datetime, float]] = []
        for ts, value in rows:
            parsed.append((datetime.fromisoformat(ts), float(value)))
        return parsed

    def _query_metrics(self, start: datetime) -> QueryMetrics:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT intent, latency_ms, success
                FROM query_logs
                WHERE timestamp >= ?
                """,
                (start.isoformat(),),
            ).fetchall()
        total = len(rows)
        if total == 0:
            return QueryMetrics()
        latencies = [float(row[1]) for row in rows]
        success = sum(1 for row in rows if row[2] == 1)
        failed = total - success
        by_intent: dict[str, int] = {}
        for intent, _, _ in rows:
            if intent:
                by_intent[intent] = by_intent.get(intent, 0) + 1
        return QueryMetrics(
            total=total,
            success=success,
            failed=failed,
            avg_latency_ms=_average(latencies),
            p95_latency_ms=_percentile(latencies, 95),
            p99_latency_ms=_percentile(latencies, 99),
            by_intent=by_intent,
        )

    def _ingestion_metrics(self, start: datetime) -> IngestionMetrics:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT documents_loaded, chunks_stored, duration_seconds, errors, timestamp
                FROM ingestion_logs
                WHERE timestamp >= ?
                """,
                (start.isoformat(),),
            ).fetchall()
        if not rows:
            return IngestionMetrics()
        total_runs = len(rows)
        total_documents = sum(int(row[0]) for row in rows)
        total_chunks = sum(int(row[1]) for row in rows)
        durations = [float(row[2]) for row in rows]
        errors = sum(int(row[3]) for row in rows)
        last_run = max(datetime.fromisoformat(row[4]) for row in rows)
        return IngestionMetrics(
            total_runs=total_runs,
            total_documents=total_documents,
            total_chunks=total_chunks,
            avg_duration_seconds=_average(durations),
            last_run=last_run,
            errors=errors,
        )

    def _component_metrics(self, start: datetime) -> dict[str, ComponentMetrics]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT component, latency_ms, success, error
                FROM component_logs
                WHERE timestamp >= ?
                """,
                (start.isoformat(),),
            ).fetchall()
        aggregated: dict[str, dict[str, Any]] = {}
        for component, latency, success, error in rows:
            entry = aggregated.setdefault(
                component,
                {"latencies": [], "calls": 0, "errors": 0, "last_error": None},
            )
            entry["latencies"].append(float(latency))
            entry["calls"] += 1
            if success == 0:
                entry["errors"] += 1
                entry["last_error"] = error
        output: dict[str, ComponentMetrics] = {}
        for component, data in aggregated.items():
            output[component] = ComponentMetrics(
                name=component,
                calls=data["calls"],
                errors=data["errors"],
                avg_latency_ms=_average(data["latencies"]),
                last_error=data["last_error"],
            )
        return output


@contextmanager
def record_component(metrics: MetricsCollector, name: str) -> Iterator[None]:
    start = datetime.now(timezone.utc)
    error: str | None = None
    try:
        yield None
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        raise
    finally:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000.0
        metrics.record_component_call(name, elapsed, error is None, error)


def _period_start(period: str) -> datetime:
    delta = _parse_interval(period)
    return datetime.now(timezone.utc) - delta


def _parse_interval(value: str) -> timedelta:
    number, unit = _split_period(value)
    if unit == "h":
        return timedelta(hours=number)
    if unit == "d":
        return timedelta(days=number)
    if unit == "m":
        return timedelta(minutes=number)
    raise ValueError(f"Unsupported interval: {value}")


def _split_period(value: str) -> tuple[int, str]:
    value = value.strip()
    if len(value) < 2:
        raise ValueError(f"Invalid period: {value}")
    number = int(value[:-1])
    unit = value[-1]
    return number, unit


def _floor_time(ts: datetime, delta: timedelta) -> datetime:
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return ts
    epoch = int(ts.timestamp())
    bucket = epoch - (epoch % seconds)
    return datetime.fromtimestamp(bucket)


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    index = max(int(round((percentile / 100) * (len(sorted_vals) - 1))), 0)
    return float(sorted_vals[index])
