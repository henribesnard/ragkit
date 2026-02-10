"""Advanced PDF parser with OCR, tables, and images."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ragkit.config.schema_v2 import DocumentParsingConfig
from ragkit.ingestion.parsers.image_processor import ImageProcessor
from ragkit.ingestion.parsers.table_extractor import TableExtractor
from ragkit.utils.ocr import OCREngine

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Parsed document with page-level metadata."""

    content: str
    metadata: dict[str, Any]
    pages: list[dict[str, Any]] = field(default_factory=list)


class AdvancedPDFParser:
    """PDF parser with OCR, table extraction, and image handling."""

    def __init__(self, config: DocumentParsingConfig) -> None:
        self.config = config
        self._ocr_engine: OCREngine | None = None
        self._table_extractor = TableExtractor(config)
        self._image_processor = ImageProcessor(config)

    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a PDF file with all advanced capabilities."""
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {file_path}")

        try:
            import pdfplumber
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("pdfplumber is required for AdvancedPDFParser") from exc

        logger.info("Parsing PDF: %s", file_path)

        pages: list[dict[str, Any]] = []
        total_text_extracted = 0

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                logger.debug("Processing page %s/%s", page_num, len(pdf.pages))
                page_data = await self._parse_page(page, page_num)

                if (
                    self.config.skip_empty_pages
                    and len(page_data["text"].strip()) < self.config.min_text_length
                ):
                    logger.debug("Skipping empty page %s", page_num)
                    continue

                pages.append(page_data)
                total_text_extracted += len(page_data["text"])

        full_content = self._merge_pages(pages)

        metadata = {
            "source_file": str(file_path),
            "total_pages": len(pages),
            "total_characters": total_text_extracted,
            "has_tables": any(p.get("tables") for p in pages),
            "has_images": any(p.get("images") for p in pages),
            "extraction_method": self.config.pdf_extraction_method,
        }

        logger.info("PDF parsed: %s pages, %s chars", len(pages), total_text_extracted)

        return ParsedDocument(content=full_content, metadata=metadata, pages=pages)

    async def _parse_page(self, page: Any, page_num: int) -> dict[str, Any]:
        """Parse a single PDF page."""
        text = page.extract_text() or ""

        if (not text or len(text.strip()) < 10) and self.config.ocr_enabled:
            logger.info("Page %s appears scanned, running OCR", page_num)
            text = await self._ocr_page(page)

        tables: list[dict[str, Any]] = []
        if self.config.table_extraction_strategy != "none":
            tables = await self._table_extractor.extract_tables(page)

        images: list[dict[str, Any]] = []
        if self.config.image_extraction_enabled:
            images = await self._image_processor.extract_images(page, page_num)

        if self.config.image_captioning_enabled and images:
            for img in images:
                if img.get("data"):
                    img["caption"] = await self._image_processor.generate_caption(img["data"])

        if self.config.footer_removal:
            text = self._remove_footer(text)
        if self.config.page_number_removal:
            text = self._remove_page_number(text, page_num)

        headers: list[dict[str, Any]] = []
        if self.config.header_detection:
            headers = self._detect_headers(text)

        return {
            "page_number": page_num,
            "text": text,
            "tables": tables,
            "images": images,
            "headers": headers,
            "metadata": {
                "width": getattr(page, "width", None),
                "height": getattr(page, "height", None),
                "char_count": len(text),
            },
        }

    async def _ocr_page(self, page: Any) -> str:
        """Run OCR on a page image."""
        if self._ocr_engine is None:
            self._ocr_engine = OCREngine(
                engine=self.config.ocr_engine,
                languages=self.config.ocr_language,
                dpi=self.config.ocr_dpi,
                preprocessing=self.config.ocr_preprocessing,
            )

        image = page.to_image(resolution=self.config.ocr_dpi).original
        text, confidence = await self._ocr_engine.extract_text(image)

        if confidence < self.config.ocr_confidence_threshold:
            logger.warning(
                "Low OCR confidence: %.2f (threshold: %.2f)",
                confidence,
                self.config.ocr_confidence_threshold,
            )

        return text

    def _merge_pages(self, pages: list[dict[str, Any]]) -> str:
        """Merge page contents into a single string."""
        full_text: list[str] = []

        for page in pages:
            if self.config.preserve_formatting:
                full_text.append(f"\n\n--- Page {page['page_number']} ---\n\n")

            full_text.append(page.get("text", ""))

            if self.config.table_extraction_strategy == "separate":
                for table in page.get("tables", []):
                    if table.get("type") == "separate_chunk":
                        full_text.append(f"\n\n[TABLE]\n{table['content']}\n")

        return "".join(full_text)

    def _table_to_markdown(self, table: list[list[Any]]) -> str:
        """Expose markdown conversion for testing convenience."""
        return self._table_extractor._table_to_markdown(table)

    def _table_to_text(self, table: list[list[Any]]) -> str:
        """Expose text conversion for testing convenience."""
        return self._table_extractor._table_to_text(table)

    def _remove_footer(self, text: str) -> str:
        """Remove a simple footer line heuristic."""
        lines = text.split("\n")
        if lines and len(lines[-1].strip()) < 50:
            return "\n".join(lines[:-1])
        return text

    def _remove_page_number(self, text: str, page_num: int) -> str:
        """Remove page number occurrences from text."""
        patterns = {str(page_num), f"Page {page_num}", f"page {page_num}"}
        lines = [line for line in text.split("\n") if line.strip() not in patterns]
        return "\n".join(lines)

    def _detect_headers(self, text: str) -> list[dict[str, Any]]:
        """Detect simple headers in the page text."""
        headers: list[dict[str, Any]] = []
        for idx, line in enumerate(text.split("\n")):
            cleaned = line.strip()
            if not cleaned:
                continue
            if len(cleaned) > 120:
                continue
            if cleaned.isupper() or cleaned.startswith(("CHAPTER", "SECTION")):
                headers.append({"text": cleaned, "line": idx})
                continue
            if cleaned[0].isdigit() and len(cleaned.split()) <= 6:
                headers.append({"text": cleaned, "line": idx})

        return headers
