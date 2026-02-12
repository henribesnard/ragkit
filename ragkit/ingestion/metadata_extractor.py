"""Automatic metadata extraction from raw and parsed documents."""

from __future__ import annotations

import logging
import mimetypes
import re
from datetime import datetime, timezone
from pathlib import Path

from ragkit.ingestion.metadata import DocumentMetadata
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.ingestion.sources.base import RawDocument

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Build a :class:`DocumentMetadata` by inspecting a raw and parsed document."""

    def extract(
        self,
        raw_doc: RawDocument,
        parsed_doc: ParsedDocument,
        *,
        defaults: dict | None = None,
    ) -> DocumentMetadata:
        """Construct *DocumentMetadata* from a raw and parsed document.

        Parameters
        ----------
        raw_doc:
            The raw document loaded from source.
        parsed_doc:
            The document after parsing.
        defaults:
            Optional default values for tenant, domain, tags, etc.
        """
        defaults = defaults or {}
        source_path = raw_doc.source_path
        source = Path(source_path).name
        source_type = raw_doc.file_type or Path(source_path).suffix.lstrip(".")

        content = parsed_doc.content or ""
        counts = self._count_content(content)

        # File timestamps from raw metadata
        created_at = self._timestamp_from_meta(raw_doc.metadata, "created_time")
        modified_at = self._timestamp_from_meta(raw_doc.metadata, "modified_time")

        return DocumentMetadata(
            # Hierarchy
            tenant=defaults.get("tenant", "default"),
            domain=defaults.get("domain", "general"),
            subdomain=defaults.get("subdomain"),
            # Identification
            title=self._detect_title(parsed_doc, raw_doc),
            author=self._detect_author(raw_doc),
            source=source,
            source_path=source_path,
            source_type=source_type,
            mime_type=self._detect_mime_type(source_path),
            # Temporality
            created_at=created_at,
            modified_at=modified_at,
            ingested_at=datetime.now(timezone.utc),
            # Content features
            language=self._detect_language(content),
            word_count=counts["word_count"],
            char_count=counts["char_count"],
            has_tables=counts["has_tables"],
            has_images=counts["has_images"],
            has_code=counts["has_code"],
            page_count=raw_doc.metadata.get("page_count"),
            # Classification defaults
            tags=defaults.get("tags", []),
            category=defaults.get("category"),
            confidentiality=defaults.get("confidentiality", "internal"),
            # Parsing
            parser_engine=raw_doc.metadata.get("parser_engine"),
            ocr_applied=raw_doc.metadata.get("ocr_applied", False),
            parsing_quality=raw_doc.metadata.get("parsing_quality"),
            parsing_warnings=raw_doc.metadata.get("parsing_warnings", []),
        )

    # ── Private helpers ───────────────────────────────────────────────

    def _detect_title(self, parsed_doc: ParsedDocument, raw_doc: RawDocument) -> str | None:
        """Extract the title from the first H1 section or fall back to filename."""
        # Try structured sections (H1)
        if parsed_doc.structure:
            for section in parsed_doc.structure:
                if section.level == 1 and section.title:
                    return section.title.strip()

        # Try first line if it looks like a title (short, no period)
        if parsed_doc.content:
            first_line = parsed_doc.content.strip().split("\n", 1)[0].strip()
            # Strip leading markdown heading markers
            clean = re.sub(r"^#+\s*", "", first_line)
            if clean and len(clean) < 200 and "." not in clean:
                return clean

        # Fall back to file name without extension
        name = Path(raw_doc.source_path).stem
        return name if name else None

    def _detect_author(self, raw_doc: RawDocument) -> str | None:
        """Extract the author from document metadata (PDF / DOCX)."""
        meta = raw_doc.metadata
        for key in ("author", "Author", "creator", "Creator", "dc:creator"):
            value = meta.get(key)
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _detect_language(self, text: str) -> str | None:
        """Detect language using langdetect (best-effort)."""
        if not text or len(text) < 50:
            return None
        try:
            from langdetect import detect

            return detect(text)
        except Exception:  # noqa: BLE001
            logger.debug("Language detection failed, returning None")
            return None

    def _count_content(self, text: str) -> dict:
        """Compute word/char counts and detect tables, images, code blocks."""
        words = text.split()
        return {
            "word_count": len(words),
            "char_count": len(text),
            "has_tables": bool(re.search(r"\|.*\|.*\|", text)),
            "has_images": bool(re.search(r"!\[.*?\]\(.*?\)", text)),
            "has_code": bool(re.search(r"```", text)),
        }

    def _detect_mime_type(self, source_path: str) -> str | None:
        """Guess MIME type from file extension."""
        mime, _ = mimetypes.guess_type(source_path)
        return mime

    @staticmethod
    def _timestamp_from_meta(meta: dict, key: str) -> datetime | None:
        """Convert a numeric timestamp from metadata to a datetime."""
        value = meta.get(key)
        if value is None:
            return None
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            return None
