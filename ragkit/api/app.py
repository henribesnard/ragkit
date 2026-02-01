"""FastAPI app factory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from ragkit.agents import AgentOrchestrator
from ragkit.api.routes.admin import admin_router
from ragkit.api.routes.admin.websocket import router as ws_router
from ragkit.api.routes.health import router as health_router
from ragkit.api.routes.query import router as query_router
from ragkit.api.routes.status import router as status_router
from ragkit.config.schema import RAGKitConfig
from ragkit.metrics import MetricsCollector
from ragkit.state import StateStore


def create_app(
    config: RAGKitConfig,
    orchestrator: AgentOrchestrator | None = None,
    *,
    config_path: Path | None = None,
    vector_store: Any | None = None,
    embedder: Any | None = None,
    llm_router: Any | None = None,
    state_store: StateStore | None = None,
    metrics: MetricsCollector | None = None,
    setup_mode: bool = False,
    mount_ui: bool = True,
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
    app.state.setup_mode = setup_mode

    async def _sync_ingestion_status() -> None:
        if setup_mode or vector_store is None:
            return
        if not config.api.startup_sync_ingestion_status:
            return
        provider = config.vector_store.provider
        if provider == "chroma" and config.vector_store.chroma.mode != "persistent":
            return
        if provider == "qdrant" and config.vector_store.qdrant.mode == "memory":
            return
        try:
            total_chunks = await vector_store.count()
            total_documents = len(await vector_store.list_documents())
            app.state.state_store.set("total_documents", total_documents)
            app.state.state_store.set("total_chunks", total_chunks)
        except Exception:  # noqa: BLE001
            pass

    class SetupModeGuard(BaseHTTPMiddleware):
        BLOCKED_PREFIXES = ("/api/v1/query",)
        BLOCKED_EXACT = {"/api/v1/admin/ingestion/run"}

        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
            if request.app.state.setup_mode:
                path = request.url.path
                if any(path.startswith(prefix) for prefix in self.BLOCKED_PREFIXES):
                    return JSONResponse(
                        status_code=503,
                        content={
                            "detail": "Server is in setup mode. Configure via the UI first.",
                        },
                    )
                if path in self.BLOCKED_EXACT and request.method == "POST":
                    return JSONResponse(
                        status_code=503,
                        content={
                            "detail": "Server is in setup mode. Configure via the UI first.",
                        },
                    )
            return await call_next(request)

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
    app.include_router(status_router)

    app.add_event_handler("startup", _sync_ingestion_status)

    if setup_mode:
        app.add_middleware(SetupModeGuard)

    frontend_path = Path(__file__).resolve().parent.parent / "ui" / "dist"
    if mount_ui and frontend_path.exists():
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

    return app
