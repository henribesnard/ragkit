"""PDF parser implementation."""

from __future__ import annotations

import io

from ragkit.config.schema import ParsingConfig
from ragkit.exceptions import IngestionError
from ragkit.ingestion.parsers.base import BaseParser, ParsedDocument
from ragkit.ingestion.sources.base import RawDocument


def _extract_with_unstructured(raw_bytes: bytes, config: ParsingConfig) -> str | None:
    try:
        from unstructured.partition.pdf import partition_pdf
    except Exception:
        return None

    kwargs: dict[str, object] = {"file": io.BytesIO(raw_bytes)}
    if config.ocr.enabled:
        if config.ocr.languages:
            kwargs["ocr_languages"] = config.ocr.languages
        kwargs["strategy"] = "ocr_only"
    try:
        elements = partition_pdf(**kwargs)
    except TypeError:
        elements = partition_pdf(file=io.BytesIO(raw_bytes))
    parts: list[str] = []
    for element in elements:
        text = getattr(element, "text", None)
        if text:
            parts.append(text)
        else:
            parts.append(str(element))
    return "\n".join(parts).strip()


def _extract_with_pypdf(raw_bytes: bytes) -> str | None:
    try:
        from pypdf import PdfReader
    except Exception:
        return None

    reader = PdfReader(io.BytesIO(raw_bytes))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n".join(parts).strip()


def _fallback_decode(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8", errors="ignore") or raw_bytes.decode(
        "latin-1", errors="ignore"
    )


class PDFParser(BaseParser):
    def __init__(self, config: ParsingConfig | None = None):
        self.config = config or ParsingConfig()

    def supports(self, file_type: str) -> bool:
        return file_type.lower() == "pdf"

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        content = raw_doc.content
        text: str
        if isinstance(content, str):
            text = content
        else:
            engine = (self.config.engine or "auto").lower()
            if self.config.ocr.enabled and engine not in {"auto", "unstructured"}:
                raise IngestionError("OCR is only supported with the unstructured engine")
            if engine == "docling":
                raise IngestionError("docling engine is not supported for PDF parsing")
            if engine == "pypdf":
                text = _extract_with_pypdf(content) or _fallback_decode(content)
            elif engine == "unstructured":
                text = _extract_with_unstructured(content, self.config) or _fallback_decode(content)
            else:
                text = (
                    _extract_with_unstructured(content, self.config)
                    or _extract_with_pypdf(content)
                    or _fallback_decode(content)
                )

        metadata = dict(raw_doc.metadata)
        metadata.setdefault("file_type", "pdf")
        return ParsedDocument(content=text, metadata=metadata, structure=None)
