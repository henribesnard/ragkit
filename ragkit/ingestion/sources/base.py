"""Source loaders for ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    content: bytes | str
    source_path: str
    file_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseSourceLoader(ABC):
    @abstractmethod
    async def load(self) -> AsyncIterator[RawDocument]:
        """Load documents from the source."""

    @abstractmethod
    def supports(self, source_config: Any) -> bool:
        """Return whether the loader supports the given config."""
