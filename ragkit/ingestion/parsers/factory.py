# ragkit/ingestion/parsers/factory.py
import os
from typing import Any
from .text import TextParser
from .markdown import MarkdownParser
from .pdf import PDFParser
from .base import BaseParser

class ParserFactory:
    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.parsers = [
            TextParser(self.config),
            MarkdownParser(self.config),
            PDFParser(self.config)
        ]

    def get_parser(self, file_path: str) -> BaseParser:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '':
             # Handle files without extension as text if needed, or raise error
             pass

        for parser in self.parsers:
            if parser.supports(ext):
                return parser
        
        # Fallback to text parser if no match? or raise error
        return TextParser(self.config)
