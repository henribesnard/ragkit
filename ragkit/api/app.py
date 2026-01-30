"""FastAPI app factory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ragkit.agents import AgentOrchestrator
from ragkit.api.routes.admin import admin_router
from ragkit.api.routes.admin.websocket import router as ws_router
from ragkit.api.routes.health import router as health_router
from ragkit.api.routes.query import router as query_router
from ragkit.config.schema import RAGKitConfig
from ragkit.metrics import MetricsCollector
from ragkit.state import StateStore


def create_app(
    config: RAGKitConfig,
    orchestrator: AgentOrchestrator,
    *,
    config_path: Path | None = None,
    vector_store: Any | None = None,
    embedder: Any | None = None,
    llm_router: Any | None = None,
    state_store: StateStore | None = None,
    metrics: MetricsCollector | None = None,
) -> FastAPI:
    app = FastAPI(
        title="RAGKIT API",
        version="1.0.0",
        docs_url="/api/docs" if config.api.docs.enabled else None,
    )

    app.state.orchestrator = orchestrator
    app.state.config = config
    app.state.config_path = config_path or Path("ragkit.yaml")
    app.state.config_loaded_at = datetime.now(timezone.utc)
    app.state.state_store = state_store or StateStore()
    app.state.metrics = metrics or MetricsCollector()
    app.state.vector_store = vector_store
    app.state.embedder = embedder
    app.state.llm_router = llm_router

    if config.api.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.api.cors.origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(query_router, prefix="/api/v1")
    app.include_router(health_router)
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1/admin")

    frontend_path = Path(__file__).resolve().parent.parent / "ui" / "dist"
    if frontend_path.exists():
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

    return app
