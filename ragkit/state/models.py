"""State models for RAGKIT runtime."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ComponentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth(BaseModel):
    name: str
    status: ComponentStatus
    latency_ms: float | None = None
    last_check: datetime
    message: str | None = None
    details: dict | None = None


class SystemHealth(BaseModel):
    overall: ComponentStatus
    components: dict[str, ComponentHealth]
    checked_at: datetime


class IngestionState(BaseModel):
    last_run: datetime | None = None
    last_stats: dict | None = None
    is_running: bool = False
    pending_documents: int = 0
    total_documents: int = 0
    total_chunks: int = 0


class SystemState(BaseModel):
    started_at: datetime
    config_loaded_at: datetime
    ingestion: IngestionState
    health: SystemHealth
    version: str = "1.0.0"
