"""Table extraction utilities for advanced parsing."""

from __future__ import annotations

import logging
from typing import Any

from ragkit.config.schema_v2 import DocumentParsingConfig

logger = logging.getLogger(__name__)


class TableExtractor:
    """Extracts tables using multiple strategies."""

    def __init__(self, config: DocumentParsingConfig) -> None:
        self.config = config

    async def extract_tables(self, page: Any) -> list[dict[str, Any]]:
        """Extract tables from a pdfplumber page."""
        strategy = self.config.table_extraction_strategy
        if strategy == "none":
            return []

        if strategy == "vision":
            return await self._extract_tables_vision(page)

        try:
            tables = page.find_tables()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Table extraction failed: %s", exc)
            return []

        results: list[dict[str, Any]] = []
        for idx, table in enumerate(tables):
            extracted_table = table.extract()
            if not extracted_table:
                continue

            if len(extracted_table) > self.config.table_max_rows:
                logger.warning("Table %s exceeds max rows; truncating", idx)
                extracted_table = extracted_table[: self.config.table_max_rows]

            if extracted_table and len(extracted_table[0]) > self.config.table_max_columns:
                logger.warning("Table %s exceeds max columns; truncating", idx)
                extracted_table = [row[: self.config.table_max_columns] for row in extracted_table]

            if strategy == "markdown":
                results.append(
                    {
                        "type": "markdown",
                        "content": self._table_to_markdown(extracted_table),
                        "bbox": table.bbox,
                    }
                )
            elif strategy == "preserve":
                results.append(
                    {
                        "type": "structured",
                        "rows": extracted_table,
                        "bbox": table.bbox,
                    }
                )
            elif strategy == "separate":
                results.append(
                    {
                        "type": "separate_chunk",
                        "content": self._table_to_text(extracted_table),
                        "bbox": table.bbox,
                    }
                )

        return results

    async def _extract_tables_vision(self, page: Any) -> list[dict[str, Any]]:
        """Placeholder for vision-based table extraction."""
        logger.warning("Vision table extraction is not implemented")
        return []

    def _table_to_markdown(self, table: list[list[Any]]) -> str:
        """Convert a table to markdown format."""
        if not table:
            return ""

        header = "| " + " | ".join(str(cell) for cell in table[0]) + " |"
        separator = "| " + " | ".join("---" for _ in table[0]) + " |"
        rows = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in table[1:]]

        return "\n".join([header, separator] + rows)

    def _table_to_text(self, table: list[list[Any]]) -> str:
        """Convert a table to plain text lines."""
        return "\n".join(" | ".join(str(cell) for cell in row) for row in table)
