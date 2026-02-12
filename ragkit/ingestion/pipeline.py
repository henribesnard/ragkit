# ragkit/ingestion/pipeline.py
from typing import Any
from ragkit.models import Document
from ragkit.ingestion.parsers.factory import ParserFactory
from ragkit.ingestion.preprocessing import TextPreprocessor
from ragkit.ingestion.metadata import MetadataExtractor

class IngestionPipeline:
    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.parser_factory = ParserFactory(self.config.get('parsing', {}))
        self.preprocessor = TextPreprocessor(self.config.get('preprocessing', {}))
        self.metadata_extractor = MetadataExtractor()

    def run(self, file_path: str) -> Document:
        # 1. Extract base metadata
        metadata = self.metadata_extractor.extract_from_file(file_path)
        
        # 2. Parse content
        parser = self.parser_factory.get_parser(file_path)
        doc = parser.parse(file_path, metadata)
        doc.metadata.parser_engine = parser.__class__.__name__
        
        # 3. Preprocess text
        doc = self.preprocessor.process(doc)
        
        # 4. Enrich metadata (stats)
        doc = self.metadata_extractor.enrich(doc)
        
        return doc
