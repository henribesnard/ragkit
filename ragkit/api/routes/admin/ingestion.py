"""Admin ingestion endpoints."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ragkit.api.routes.admin.websocket import broadcast_event
from ragkit.config.schema import RAGKitConfig
from ragkit.ingestion import IngestionPipeline
from ragkit.state import StateStore

router = APIRouter(prefix="/ingestion")


class IngestionStatus(BaseModel):
    is_running: bool
    last_run: datetime | None
    last_stats: dict | None
    pending_documents: int
    total_documents: int
    total_chunks: int


class IngestionRunRequest(BaseModel):
    incremental: bool = True
    sources: list[str] | None = None


class IngestionRunResponse(BaseModel):
    job_id: str
    status: str
    message: str


_ingestion_jobs: dict[str, dict] = {}


@router.get("/status", response_model=IngestionStatus)
async def get_ingestion_status(request: Request) -> IngestionStatus:
    state: StateStore = request.app.state.state_store
    config = request.app.state.config

    pending = _count_pending_documents(config, state_file=Path(".ragkit") / "ingestion_state.json")

    last_run_raw = state.get("last_ingestion_time")
    last_run = datetime.fromisoformat(last_run_raw) if last_run_raw else None

    return IngestionStatus(
        is_running=bool(state.get("ingestion_running", False)),
        last_run=last_run,
        last_stats=state.get("last_ingestion_stats"),
        pending_documents=pending,
        total_documents=int(state.get("total_documents", 0)),
        total_chunks=int(state.get("total_chunks", 0)),
    )


@router.post("/run", response_model=IngestionRunResponse)
async def run_ingestion(payload: IngestionRunRequest, request: Request) -> IngestionRunResponse:
    state: StateStore = request.app.state.state_store
    if state.get("ingestion_running", False):
        raise HTTPException(status_code=409, detail="Ingestion already in progress")

    job_id = f"ingest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    _ingestion_jobs[job_id] = {"status": "running"}

    async def run_pipeline() -> None:
        state.set("ingestion_running", True)
        start_time = datetime.now(timezone.utc)
        try:
            await broadcast_event(
                "ingestion_started", {"job_id": job_id, "started_at": start_time.isoformat()}
            )
            pipeline = IngestionPipeline(
                request.app.state.config.ingestion,
                embedder=request.app.state.embedder,
                vector_store=request.app.state.vector_store,
            )
            stats = await pipeline.run(incremental=payload.incremental)
            metrics_collector = getattr(request.app.state, "metrics", None)
            if metrics_collector is not None:
                metrics_collector.record_ingestion(stats)

            state.set("last_ingestion_time", datetime.now(timezone.utc).isoformat())
            state.set("last_ingestion_stats", stats.model_dump())

            total_documents = stats.documents_loaded
            total_chunks = stats.chunks_stored
            vector_store = getattr(request.app.state, "vector_store", None)
            if vector_store is not None:
                try:
                    total_chunks = await vector_store.count()
                    total_documents = len(await vector_store.list_documents())
                except Exception:  # noqa: BLE001
                    pass

            state.set("total_documents", total_documents)
            state.set("total_chunks", total_chunks)

            orchestrator = getattr(request.app.state, "orchestrator", None)
            if orchestrator is not None:
                try:
                    await orchestrator.retrieval.refresh_lexical_index()
                except Exception:  # noqa: BLE001
                    pass

            state.add_ingestion_run(
                stats=stats.model_dump(),
                status="completed",
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
            )
            _ingestion_jobs[job_id] = {"status": "completed", "stats": stats.model_dump()}
            await broadcast_event(
                "ingestion_completed",
                {
                    "job_id": job_id,
                    "stats": stats.model_dump(),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            _ingestion_jobs[job_id] = {"status": "failed", "error": str(exc)}
            state.add_ingestion_run(
                stats={"error": str(exc)},
                status="failed",
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
            )
            await broadcast_event(
                "ingestion_failed",
                {
                    "job_id": job_id,
                    "error": str(exc),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        finally:
            state.set("ingestion_running", False)

    asyncio.create_task(run_pipeline())

    return IngestionRunResponse(
        job_id=job_id,
        status="started",
        message="Ingestion started in background",
    )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict:
    if job_id not in _ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return _ingestion_jobs[job_id]


@router.get("/history")
async def get_ingestion_history(request: Request, limit: int = 10) -> list[dict]:
    state: StateStore = request.app.state.state_store
    return state.get_ingestion_history(limit)


def _count_pending_documents(config: RAGKitConfig, state_file: Path) -> int:
    state = _load_state(state_file)
    pending = 0
    if config.ingestion is None:
        return pending
    for source in config.ingestion.sources:
        if source.type != "local":
            continue
        for path in _iter_source_files(Path(source.path), source.patterns, source.recursive):
            if not path.is_file():
                continue
            mtime = path.stat().st_mtime
            previous = state.get(str(path))
            if previous is None or mtime > float(previous):
                pending += 1
    return pending


def _iter_source_files(base: Path, patterns: list[str], recursive: bool) -> list[Path]:
    if not base.exists():
        return []
    if not patterns:
        patterns = ["*"]
    files: list[Path] = []
    for pattern in patterns:
        if recursive:
            files.extend(base.rglob(pattern))
        else:
            files.extend(base.glob(pattern))
    return files


def _load_state(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): float(value) for key, value in data.items()}
