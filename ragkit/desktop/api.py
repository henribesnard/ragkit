# ragkit/desktop/api.py
from typing import Any
from ragkit.ingestion.pipeline import IngestionPipeline

def preview_ingestion(file_path: str, config: dict[str, Any]) -> dict[str, Any]:
    """Exécute le pipeline d'ingestion et retourne le résultat pour prévisualisation."""
    pipeline = IngestionPipeline(config)
    doc = pipeline.run(file_path)
    
    return {
        "raw_content": doc.raw_content,
        "cleaned_content": doc.content,
        "metadata": doc.metadata.dict(),
        "preview_success": True
    }
