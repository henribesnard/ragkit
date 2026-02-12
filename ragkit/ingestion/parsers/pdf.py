# ragkit/ingestion/parsers/pdf.py
import os
# import pypdf  # To be added to requirements
from ragkit.models import Document, DocumentMetadata
from .base import BaseParser

class PDFParser(BaseParser):
    def parse(self, file_path: str, metadata: DocumentMetadata) -> Document:
        # Placeholder for PDF extraction logic
        # In a real implementation we would use pypdf or PyMuPDF here
        config = self.config or {}
        
        content = f"[MOCK] Contenu extrait du PDF {os.path.basename(file_path)}"
        if config.get('ocr_enabled', False):
            content += "\n[OCR] OCR appliqué sur les images."
            metadata.ocr_applied = True
        
        metadata.page_count = 10 # Mock
        
        return Document(
            content=content,
            raw_content=content,
            metadata=metadata
        )

    def supports(self, file_extension: str) -> bool:
        return file_extension.lower() == ".pdf"
