"""Parser factory and exports."""

from __future__ import annotations

from ragkit.config.schema import ParsingConfig
from ragkit.ingestion.parsers.advanced_pdf_parser import AdvancedPDFParser
from ragkit.ingestion.parsers.advanced_pdf_parser import ParsedDocument as AdvancedParsedDocument
from ragkit.ingestion.parsers.base import BaseParser, ParsedDocument
from ragkit.ingestion.parsers.docx import DOCXParser
from ragkit.ingestion.parsers.image_processor import ImageProcessor
from ragkit.ingestion.parsers.markdown import MarkdownParser
from ragkit.ingestion.parsers.pdf import PDFParser
from ragkit.ingestion.parsers.table_extractor import TableExtractor
from ragkit.ingestion.parsers.text import TextParser
from ragkit.ingestion.sources.base import RawDocument


class ParserRouter(BaseParser):
    def __init__(self, parsers: list[BaseParser]):
        self.parsers = parsers

    def supports(self, file_type: str) -> bool:
        return any(parser.supports(file_type) for parser in self.parsers)

    async def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        for parser in self.parsers:
            if parser.supports(raw_doc.file_type):
                return await parser.parse(raw_doc)
        # Fallback to text parser if none match
        return await TextParser().parse(raw_doc)


def create_parser(config: ParsingConfig | None = None) -> BaseParser:
    cfg = config or ParsingConfig()
    parsers: list[BaseParser] = [
        PDFParser(cfg),
        DOCXParser(cfg),
        MarkdownParser(cfg),
        TextParser(cfg),
    ]
    return ParserRouter(parsers)


__all__ = [
    "BaseParser",
    "ParserRouter",
    "PDFParser",
    "AdvancedPDFParser",
    "AdvancedParsedDocument",
    "TableExtractor",
    "ImageProcessor",
    "DOCXParser",
    "MarkdownParser",
    "TextParser",
    "create_parser",
]
