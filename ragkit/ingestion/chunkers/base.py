"""Chunking base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.models import Chunk


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Split a document into chunks."""
