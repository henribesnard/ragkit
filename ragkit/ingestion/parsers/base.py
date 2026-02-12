# ragkit/ingestion/parsers/base.py
from abc import ABC, abstractmethod
from typing import Any
from ragkit.models import Document, DocumentMetadata

class BaseParser(ABC):
    """Interface commune pour tous les parsers."""

    def __init__(self, config: Any = None):
        self.config = config

    @abstractmethod
    def parse(self, file_path: str, metadata: DocumentMetadata) -> Document:
        """Parse un fichier et retourne un Document."""
        ...

    def supports(self, file_extension: str) -> bool:
        """Retourne True si ce parser supporte l'extension."""
        return False
