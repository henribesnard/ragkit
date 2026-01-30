"""Plain text parser implementation."""

from __future__ import annotations

from ragkit.config.schema import ParsingConfig
from ragkit.ingestion.parsers.base import BaseParser, ParsedDocument
from ragkit.ingestion.sources.base import RawDocument


class TextParser(BaseParser):
    def __init__(self, config: ParsingConfig | None = None):
        self.config = config or ParsingConfig()

    def supports(self, file_type: str) -> bool:
        return file_type.lower() in {"txt", "text"}

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        content = raw_doc.content
        encoding = "utf-8"
        if isinstance(content, bytes):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                encoding = "latin-1"
                text = content.decode("latin-1", errors="ignore")
        else:
            text = content

        metadata = dict(raw_doc.metadata)
        metadata.setdefault("file_type", "txt")
        metadata["encoding"] = encoding
        return ParsedDocument(content=text, metadata=metadata, structure=None)
