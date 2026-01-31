"""Server status endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/status")
async def get_status(request: Request) -> dict:
    config = request.app.state.config
    return {
        "configured": config.is_configured,
        "setup_mode": bool(request.app.state.setup_mode),
        "version": config.version,
        "project": config.project.name,
        "components": {
            "embedding": config.embedding is not None,
            "llm": config.llm is not None,
            "agents": config.agents is not None,
            "retrieval": config.retrieval is not None,
            "ingestion": config.ingestion is not None,
            "vector_store": True,
        },
    }
