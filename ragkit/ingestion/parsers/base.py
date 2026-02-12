"""Base parser definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from ragkit.ingestion.sources.base import RawDocument


class DocumentSection(BaseModel):
    title: str | None = None
    level: int | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    structure: list[DocumentSection] | None = None


class BaseParser(ABC):
    @abstractmethod
    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        """Parse a raw document into structured text."""

    @abstractmethod
    def supports(self, file_type: str) -> bool:
        """Return whether the parser supports the given file type."""
