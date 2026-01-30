"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ragkit.agents import AgentOrchestrator
from ragkit.config.schema import RAGKitConfig
from ragkit.api.routes.health import router as health_router
from ragkit.api.routes.query import router as query_router


def create_app(config: RAGKitConfig, orchestrator: AgentOrchestrator) -> FastAPI:
    app = FastAPI(
        title="RAGKIT API",
        version="1.0.0",
        docs_url=config.api.docs.path if config.api.docs.enabled else None,
    )

    app.state.orchestrator = orchestrator
    app.state.config = config

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

    return app
