"""Markdown parser implementation."""

from __future__ import annotations

import re

from ragkit.config.schema import ParsingConfig
from ragkit.ingestion.parsers.base import BaseParser, DocumentSection, ParsedDocument
from ragkit.ingestion.sources.base import RawDocument

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _ensure_text(content: bytes | str) -> str:
    if isinstance(content, str):
        return content
    return content.decode("utf-8", errors="ignore") or content.decode("latin-1", errors="ignore")


class MarkdownParser(BaseParser):
    def __init__(self, config: ParsingConfig | None = None):
        self.config = config or ParsingConfig()

    def supports(self, file_type: str) -> bool:
        return file_type.lower() in {"md", "markdown"}

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        text = _ensure_text(raw_doc.content)
        lines = text.splitlines()

        sections: list[DocumentSection] = []
        current_title: str | None = None
        current_level: int | None = None
        buffer: list[str] = []

        def flush_section() -> None:
            nonlocal buffer, current_title, current_level
            if not buffer and current_title is None:
                return
            content = "\n".join(buffer).strip()
            if content or current_title:
                sections.append(
                    DocumentSection(
                        title=current_title,
                        level=current_level,
                        content=content,
                        metadata={},
                    )
                )
            buffer = []

        for line in lines:
            match = _HEADING_RE.match(line)
            if match:
                flush_section()
                hashes, title = match.groups()
                current_title = title.strip()
                current_level = len(hashes)
            else:
                buffer.append(line)

        flush_section()

        metadata = dict(raw_doc.metadata)
        metadata.setdefault("file_type", "md")
        return ParsedDocument(content=text, metadata=metadata, structure=sections or None)
