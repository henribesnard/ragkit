# ragkit/models.py
from datetime import datetime
from typing import Any, Literal
import uuid
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    """Metadonnées enrichies d'un document."""

    # ─── HIÉRARCHIE ORGANISATIONNELLE (configurée par l'utilisateur) ───
    tenant: str = "default"
    domain: str = ""
    subdomain: str | None = None

    # ─── IDENTIFICATION DOCUMENT (détecté automatiquement + modifiable) ───
    document_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    title: str | None = None
    author: str | None = None
    source: str = ""               # nom de fichier
    source_path: str = ""          # chemin relatif
    source_type: str = ""          # pdf, docx, md, txt, html, csv
    source_url: str | None = None
    mime_type: str | None = None

    # ─── TEMPORALITÉ (détecté automatiquement) ───
    created_at: datetime | None = None
    modified_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"

    # ─── CONTENU (auto-détecté) ───
    language: str | None = None    # ISO 639-1
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None
    has_tables: bool = False
    has_images: bool = False
    has_code: bool = False
    encoding: str = "utf-8"

    # ─── CLASSIFICATION (modifiable par l'utilisateur) ───
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    confidentiality: Literal["public", "internal", "confidential", "secret"] = "internal"
    status: Literal["draft", "review", "published", "archived"] = "published"

    # ─── PARSING (rempli par le système) ───
    parser_engine: str | None = None
    ocr_applied: bool = False
    parsing_quality: float | None = None
    parsing_warnings: list[str] = Field(default_factory=list)

    # ─── EXTENSIBLE ───
    custom: dict[str, Any] = Field(default_factory=dict)


class DocumentSection(BaseModel):
    """Section détectée dans le document."""
    title: str = ""
    level: int = 0                 # 0=titre principal, 1=H2, 2=H3...
    content: str = ""
    page_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TableData(BaseModel):
    """Tableau extrait du document."""
    page_number: int | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    caption: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Document parsé avec texte brut et métadonnées."""

    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    content: str = ""               # texte brut extrait
    raw_content: str = ""           # contenu original avant preprocessing
    
    # Métadonnées structurées
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    
    # Métadonnées legacy (pour compatibilité éventuelle)
    legacy_metadata: dict[str, Any] = Field(default_factory=dict)

    # Sections structurées (optionnel, pour header_detection)
    sections: list[DocumentSection] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)
    
    # Embedding (sera rempli plus tard)
    embedding: list[float] | None = None
