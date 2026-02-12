# ragkit/ingestion/preprocessing.py
import re
import unicodedata
from typing import Any
from ragkit.models import Document

class TextPreprocessor:
    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}

    def process(self, doc: Document) -> Document:
        text = doc.content
        
        # 1. Unicode normalization
        norm_method = self.config.get('normalize_unicode', 'NFC')
        if norm_method in ['NFC', 'NFD', 'NFKC', 'NFKD']:
            text = unicodedata.normalize(norm_method, text)

        # 2. Removing URLs
        if self.config.get('remove_urls', False):
            text = re.sub(r'https?://\S+', '', text)

        # 3. Lowercase
        if self.config.get('lowercase', False):
            text = text.lower()

        # 4. Remove punctuation (optional)
        if self.config.get('remove_punctuation', False):
            text = re.sub(r'[^\w\s]', '', text)
            
        # 5. Normalize whitespace
        if self.config.get('normalize_whitespace', True):
            text = re.sub(r'\s+', ' ', text).strip()

        doc.content = text
        return doc
