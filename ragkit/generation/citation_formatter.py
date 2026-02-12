"""Citation formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ragkit.config.schema_v2 import LLMGenerationConfigV2

_SUPERSCRIPTS = {
    0: "⁰",
    1: "¹",
    2: "²",
    3: "³",
    4: "⁴",
    5: "⁵",
    6: "⁶",
    7: "⁷",
    8: "⁸",
    9: "⁹",
}


def _to_superscript(number: int) -> str:
    digits = [int(ch) for ch in str(number)]
    return "".join(_SUPERSCRIPTS.get(d, str(d)) for d in digits)


@dataclass
class CitationParts:
    source_name: str
    page: str | None = None
    section: str | None = None
    date: str | None = None
    url: str | None = None


class CitationFormatter:
    """Formats citations and source headers for context."""

    def __init__(self, config: LLMGenerationConfigV2) -> None:
        self.config = config

    def format_citation(self, index: int, metadata: dict[str, Any] | None = None) -> str:
        """Format a citation marker for answers."""
        metadata = metadata or {}
        if self.config.citation_format == "numbered":
            return f"[{index}]"
        if self.config.citation_format == "footnote":
            return _to_superscript(index)
        return f"({self.format_inline(metadata)})"

    def format_source_header(
        self,
        index: int,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Format the context header line for a document."""
        metadata = metadata or {}
        source_label = self.format_inline(metadata)
        return f"[{index}] {source_label}"

    def format_inline(self, metadata: dict[str, Any]) -> str:
        """Format inline citation metadata."""
        parts = self._extract_parts(metadata)
        if not self.config.include_metadata_in_citation:
            return f"Source: {parts.source_name}"

        template = self.config.citation_template or "[Source: {source_name}]"
        return template.format(
            source_name=parts.source_name,
            page=parts.page or "?",
            section=parts.section or "?",
            date=parts.date or "?",
            url=parts.url or "?",
        )

    def _extract_parts(self, metadata: dict[str, Any]) -> CitationParts:
        source_name = (
            metadata.get("source_name")
            or metadata.get("source")
            or metadata.get("filename")
            or metadata.get("file_name")
            or metadata.get("path")
            or metadata.get("id")
            or "Unknown"
        )
        page = metadata.get("page") or metadata.get("page_number")
        section = metadata.get("section")
        date = metadata.get("date")
        url = metadata.get("url")
        return CitationParts(
            source_name=str(source_name),
            page=str(page) if page is not None else None,
            section=str(section) if section is not None else None,
            date=str(date) if date is not None else None,
            url=str(url) if url is not None else None,
        )
