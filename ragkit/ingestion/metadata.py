# ragkit/ingestion/metadata.py
import os
from datetime import datetime
from ragkit.models import DocumentMetadata

class MetadataExtractor:
    """Service d'extraction et d'enrichissement des métadonnées."""
    
    def extract_from_file(self, file_path: str) -> DocumentMetadata:
        """Crée les métadonnées de base à partir du fichier physique."""
        metadata = DocumentMetadata()
        
        # Infos fichier système
        abs_path = os.path.abspath(file_path)
        metadata.source = os.path.basename(file_path)
        metadata.source_path = os.path.dirname(abs_path)
        metadata.source_type = os.path.splitext(file_path)[1].lstrip('.').lower()
        
        try:
            stat = os.stat(file_path)
            metadata.modified_at = datetime.fromtimestamp(stat.st_mtime)
            metadata.created_at = datetime.fromtimestamp(stat.st_ctime)
        except OSError:
            pass # Fichier virtuel ou erreur d'accès
            
        return metadata

    def enrich(self, doc, config: dict = None):
        """Enrichit les métadonnées après parsing (word count, etc)."""
        if not doc.content:
            return doc
            
        doc.metadata.char_count = len(doc.content)
        doc.metadata.word_count = len(doc.content.split())
        
        # Auto-detect language (stub)
        # from langdetect import detect
        # doc.metadata.language = detect(doc.content)
        
        return doc
