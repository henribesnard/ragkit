"""Query API routes."""

from __future__ import annotations

from typing import Any

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ragkit.agents import AgentOrchestrator

router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    history: list[dict[str, Any]] | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def get_orchestrator(request: Request) -> AgentOrchestrator:
    return request.app.state.orchestrator


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, orchestrator: AgentOrchestrator = Depends(get_orchestrator)) -> QueryResponse:
    result = await orchestrator.process(request.query, request.history)
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
        raise HTTPException(status_code=404, detail="Streaming disabled")

    async def event_stream():
        result = await orchestrator.process(request.query, request.history)
        response_text = result.response.content
        if result.response.sources:
            sources = "\n".join(f"- {source}" for source in result.response.sources)
            response_text += f"\n\nSources:\n{sources}"

        chunk_size = 50
        for start in range(0, len(response_text), chunk_size):
            chunk = response_text[start : start + chunk_size]
            payload = json.dumps({"content": chunk, "done": False})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0)

        payload = json.dumps({"content": "", "done": True})
        yield f"data: {payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
