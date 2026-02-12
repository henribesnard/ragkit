# ragkit/ingestion/parsers/markdown.py
import os
from ragkit.models import Document, DocumentMetadata
from .base import BaseParser

class MarkdownParser(BaseParser):
    def parse(self, file_path: str, metadata: DocumentMetadata) -> Document:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Simple extraction for now - could be enhanced with markdown-it-py later
        # Detect title from first H1 if not set
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                if not metadata.title:
                    metadata.title = line[2:].strip()
                break

        return Document(
            content=content,
            raw_content=content,
            metadata=metadata
        )

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".md"
