"""DOCX parser implementation."""

from __future__ import annotations

import io

from ragkit.config.schema import ParsingConfig
from ragkit.ingestion.parsers.base import BaseParser, ParsedDocument
from ragkit.ingestion.sources.base import RawDocument


def _extract_with_unstructured(raw_bytes: bytes) -> str | None:
    try:
        from unstructured.partition.docx import partition_docx  # type: ignore
    except Exception:
        return None

    elements = partition_docx(file=io.BytesIO(raw_bytes))
    parts: list[str] = []
    for element in elements:
        text = getattr(element, "text", None)
        if text:
            parts.append(text)
        else:
            parts.append(str(element))
    return "\n".join(parts).strip()


def _extract_with_python_docx(raw_bytes: bytes) -> str | None:
    try:
        import docx  # type: ignore
    except Exception:
        return None

    doc = docx.Document(io.BytesIO(raw_bytes))
    parts = [para.text for para in doc.paragraphs if para.text]
    return "\n".join(parts).strip()


def _fallback_decode(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8", errors="ignore") or raw_bytes.decode(
        "latin-1", errors="ignore"
    )


class DOCXParser(BaseParser):
    def __init__(self, config: ParsingConfig | None = None):
        self.config = config or ParsingConfig()

    def supports(self, file_type: str) -> bool:
        return file_type.lower() in {"docx", "doc"}

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        content = raw_doc.content
        if isinstance(content, str):
            text = content
        else:
            text = (
                _extract_with_unstructured(content)
                or _extract_with_python_docx(content)
                or _fallback_decode(content)
            )

        metadata = dict(raw_doc.metadata)
        metadata.setdefault("file_type", "docx")
        return ParsedDocument(content=text, metadata=metadata, structure=None)
