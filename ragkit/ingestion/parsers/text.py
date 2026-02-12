# ragkit/ingestion/parsers/text.py
import os
from ragkit.models import Document, DocumentMetadata
from .base import BaseParser

class TextParser(BaseParser):
    def parse(self, file_path: str, metadata: DocumentMetadata) -> Document:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        return Document(
            content=content,
            raw_content=content,
            metadata=metadata
        )

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".txt"
