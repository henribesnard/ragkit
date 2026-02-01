"""Query API routes."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ragkit.agents import AgentOrchestrator
from ragkit.api.routes.admin.websocket import broadcast_event

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    history: list[dict[str, Any]] | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def get_orchestrator(request: Request) -> AgentOrchestrator:
    orchestrator = request.app.state.orchestrator
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Server is in setup mode")
    return orchestrator


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest, orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> QueryResponse:
    start = time.perf_counter()
    result = await orchestrator.process(request.query, request.history)
    latency_ms = (time.perf_counter() - start) * 1000
    try:
        await broadcast_event(
            "query_received",
            {
                "query": request.query,
                "latency_ms": latency_ms,
                "intent": result.analysis.intent,
                "needs_retrieval": result.analysis.needs_retrieval,
            },
        )
    except Exception:  # noqa: BLE001
        pass
    return QueryResponse(
        answer=result.response.content,
        sources=result.response.sources,
        metadata=result.response.metadata,
    )


@router.post("/query/stream")
async def query_stream(
    request: QueryRequest,
    http_request: Request,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> StreamingResponse:
    config = http_request.app.state.config
    if not config.api.streaming.enabled:
        raise HTTPException(status_code=501, detail="Streaming is not enabled in configuration")

    async def event_stream() -> AsyncIterator[str]:
        async for event in orchestrator.process_stream(request.query, request.history):
            payload = json.dumps(event)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
