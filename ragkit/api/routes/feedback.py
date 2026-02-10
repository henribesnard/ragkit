"""Feedback API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/feedback")


class FeedbackRequest(BaseModel):
    rating: Literal["up", "down"]
    message_id: str | None = None
    comment: str | None = None
    metadata: dict[str, Any] | None = None


@router.post("")
async def submit_feedback(payload: FeedbackRequest, request: Request) -> dict[str, Any]:
    store = request.app.state.state_store
    existing: list[dict[str, Any]] = store.get("feedback", default=[])
    entry = {
        "rating": payload.rating,
        "message_id": payload.message_id,
        "comment": payload.comment,
        "metadata": payload.metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    existing.append(entry)
    store.set("feedback", existing[-500:])
    return {"status": "ok"}
