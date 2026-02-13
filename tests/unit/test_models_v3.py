import pytest
from ragkit.models import DocumentMetadata, Document
from datetime import datetime

def test_metadata_defaults():
    meta = DocumentMetadata(
        title="Test Doc",
        source="test.pdf",
        source_path="data/test.pdf",
        source_type="pdf"
    )
    
    assert meta.tenant == "default"
    assert meta.confidentiality == "internal"
    assert meta.status == "published"
    assert meta.version == "1.0"
    assert meta.ingested_at is not None
    assert meta.document_id.startswith("doc_")

def test_metadata_full_fields():
    now = datetime.utcnow()
    meta = DocumentMetadata(
        title="Report",
        source="report.docx",
        source_path="report.docx",
        source_type="docx",
        tenant="Acme Corp",
        domain="Finance",
        page_count=10,
        tags=["q1", "financial"],
        custom={"priority": "high"}
    )
    
    assert meta.tenant == "Acme Corp"
    assert meta.domain == "Finance"
    assert meta.page_count == 10
    assert "q1" in meta.tags
    assert meta.custom["priority"] == "high"

def test_document_model():
    meta = DocumentMetadata(
        title="Doc",
        source="doc.txt",
        source_path="doc.txt",
        source_type="txt"
    )
    doc = Document(
        content="Hello world",
        metadata=meta
    )
    
    assert doc.content == "Hello world"
    assert doc.metadata.title == "Doc"
    assert doc.id.startswith("doc_")
