"""Structured document metadata model for enriched ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Rich metadata extracted from a document during ingestion.

    Provides structured fields for organisational hierarchy, identification,
    temporality, auto-detected content features, classification and parsing
    info.  All fields have sensible defaults so the model can be created
    incrementally.
    """

    # ── Organisational hierarchy ──────────────────────────────────────
    tenant: str = "default"
    domain: str = "general"
    subdomain: str | None = None

    # ── Document identification ───────────────────────────────────────
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str | None = None
    author: str | None = None
    source: str = ""  # file name
    source_path: str = ""  # relative path
    source_type: str = ""  # pdf, docx, md, txt, html, csv …
    source_url: str | None = None
    mime_type: str | None = None

    # ── Temporality ───────────────────────────────────────────────────
    created_at: datetime | None = None
    modified_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"

    # ── Auto-detected content features ────────────────────────────────
    language: str | None = None  # ISO 639-1
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None
    has_tables: bool = False
    has_images: bool = False
    has_code: bool = False
    encoding: str = "utf-8"

    # ── Classification (user-modifiable) ──────────────────────────────
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    confidentiality: Literal["public", "internal", "confidential", "secret"] = "internal"
    status: Literal["draft", "review", "published", "archived"] = "published"

    # ── Parsing info (system) ─────────────────────────────────────────
    parser_engine: str | None = None
    ocr_applied: bool = False
    parsing_quality: float | None = None  # 0-1
    parsing_warnings: list[str] = Field(default_factory=list)

    # ── Extensible ────────────────────────────────────────────────────
    custom: dict[str, Any] = Field(default_factory=dict)

    def to_flat_dict(self) -> dict[str, Any]:
        """Return a flat dict suitable for chunk metadata propagation."""
        data = self.model_dump(exclude_none=True)
        # Remove heavy fields that don't belong in every chunk
        data.pop("custom", None)
        data.pop("parsing_warnings", None)
        # Serialise datetime objects to ISO strings
        for key in ("created_at", "modified_at", "ingested_at"):
            if key in data and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        return data
