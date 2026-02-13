from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid

class DocumentMetadata(BaseModel):
    """
    Rich metadata model for RAGKIT documents.
    """
    # Organization
    tenant: Optional[str] = Field(None, description="Organization or client identifier")
    domain: Optional[str] = Field(None, description="Business domain")
    subdomain: Optional[str] = Field(None, description="Business subdomain")

    # Identification
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="Document title (editable)")
    author: Optional[str] = Field(None, description="Document author (editable)")
    source: str = Field(..., description="Original filename")
    source_path: str = Field(..., description="Relative path in the source directory")
    source_type: str = Field(..., description="File extension (pdf, docx, etc.)")
    source_url: Optional[str] = Field(None, description="Original URL if applicable")
    mime_type: Optional[str] = Field(None, description="Detected MIME type")

    # Temporality
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=datetime.now)
    version: str = Field("1.0", description="Document version")

    # Content Stats
    language: Optional[str] = Field("fr", description="ISO 639-1 language code")
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    has_tables: bool = False
    has_images: bool = False
    has_code: bool = False
    encoding: Optional[str] = None

    # Classification
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    confidentiality: Literal["public", "internal", "confidential", "secret"] = "internal"
    status: Literal["draft", "review", "published", "archived"] = "published"

    # Parsing Info
    parser_engine: Optional[str] = None
    ocr_applied: bool = False
    parsing_quality: Optional[float] = None
    parsing_warnings: List[str] = Field(default_factory=list)

    # Extensible
    custom: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    text: str
    metadata: DocumentMetadata
