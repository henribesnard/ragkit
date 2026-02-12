# RAGKIT v2 — Roadmap Incrémental & Plan d'Implémentation

## Philosophie

Chaque **Étape** = un domaine fonctionnel autonome, testable, validable.
On ne passe à l'Étape N+1 que lorsque l'Étape N est **installable, testable, et validée**.
La version actuelle est archivée dans une branche `legacy/v1`.

---

# PARTIE 1 — ROADMAP COMPLET (13 Étapes)

```
Étape 1  ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  INGESTION & PREPROCESSING
Étape 2  ░░░░░░░░░░██████████░░░░░░░░░░░░░░░░░░░░░  CHUNKING
Étape 3  ░░░░░░░░░░░░░░░░░░░░██████████░░░░░░░░░░░  EMBEDDING
Étape 4  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██████████░  BASE VECTORIELLE
Étape 5  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█  RECHERCHE SÉMANTIQUE
Étape 6  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  RECHERCHE LEXICALE
Étape 7  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  RECHERCHE HYBRIDE
Étape 8  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  RERANKING
Étape 9  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  LLM / GÉNÉRATION
Étape 10 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  CACHE & PERFORMANCE
Étape 11 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  MONITORING & EVALUATION
Étape 12 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  SÉCURITÉ & COMPLIANCE
Étape 13 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  MISE À JOUR & MAINTENANCE
```

---

## Étape 1 — INGESTION & PREPROCESSING
**Livrable** : Pipeline d'ingestion qui prend un dossier de documents, les parse, les prétraite, et produit des `Document` propres avec métadonnées enrichies.
**Validation** : CLI `ragkit ingest ./docs` → affiche les documents parsés avec métadonnées.
**Estimation** : 5-7 jours

## Étape 2 — CHUNKING
**Livrable** : Module de découpage qui prend les `Document` de l'Étape 1 et produit des `Chunk` avec métadonnées héritées + enrichies.
**Validation** : CLI `ragkit ingest ./docs --show-chunks` → affiche les chunks avec stats.
**Estimation** : 4-5 jours

## Étape 3 — EMBEDDING
**Livrable** : Module d'embedding multi-provider qui vectorise les chunks.
**Validation** : CLI `ragkit embed` → vectorise les chunks, affiche dimensions et temps.
**Estimation** : 4-5 jours

## Étape 4 — BASE DE DONNÉES VECTORIELLE
**Livrable** : Adapteurs vectorstore (ChromaDB, Qdrant) avec insertion, recherche, filtrage.
**Validation** : CLI `ragkit index` → insère les embeddings, `ragkit search "query"` → résultats.
**Estimation** : 5-6 jours

## Étape 5 — RECHERCHE SÉMANTIQUE
**Livrable** : Retriever sémantique avec query processing, MMR, filtres metadata.
**Validation** : CLI `ragkit search --mode semantic "query"` → résultats scorés et diversifiés.
**Estimation** : 3-4 jours

## Étape 6 — RECHERCHE LEXICALE
**Livrable** : Retriever BM25 alimenté automatiquement depuis le vectorstore, avec tokenization configurable.
**Validation** : CLI `ragkit search --mode lexical "query"` → résultats BM25 non-vides.
**Estimation** : 3-4 jours

## Étape 7 — RECHERCHE HYBRIDE
**Livrable** : Fusion sémantique + lexicale avec RRF, weighted_sum, normalisation.
**Validation** : CLI `ragkit search --mode hybrid "query"` → résultats fusionnés.
**Estimation** : 3-4 jours

## Étape 8 — RERANKING
**Livrable** : Reranker multi-provider (Cohere, cross-encoder local) post-retrieval.
**Validation** : CLI `ragkit search --rerank "query"` → résultats réordonnés.
**Estimation** : 3-4 jours

## Étape 9 — LLM / GÉNÉRATION
**Livrable** : Pipeline RAG complet : retrieval → context → LLM → réponse avec citations.
**Validation** : CLI `ragkit query "question"` → réponse avec sources citées.
**Estimation** : 5-7 jours

## Étape 10 — CACHE & PERFORMANCE
**Livrable** : Cache requêtes, cache embeddings, async processing, warmup.
**Validation** : Benchmark avant/après sur 100 requêtes, latence p50/p95.
**Estimation** : 3-4 jours

## Étape 11 — MONITORING & EVALUATION
**Livrable** : Métriques retrieval (precision@k, recall@k, MRR), logging, feedback.
**Validation** : Dashboard métriques, `ragkit eval` sur un dataset de test.
**Estimation** : 4-5 jours

## Étape 12 — SÉCURITÉ & COMPLIANCE
**Livrable** : Contrôle d'accès, PII detection/redaction, filtres contenu.
**Validation** : Tests d'intrusion, vérification RGPD sur documents de test.
**Estimation** : 4-5 jours

## Étape 13 — MISE À JOUR & MAINTENANCE
**Livrable** : Indexation incrémentale, versioning, auto-refresh.
**Validation** : Ajout/suppression de documents sans réindexation totale.
**Estimation** : 3-4 jours

---

# PARTIE 2 — STRUCTURE DE MÉTADONNÉES PAR DÉFAUT

Cette structure est le **socle** de toute l'application. Elle est définie à l'Étape 1 et utilisée par toutes les étapes suivantes.

## Schéma `DocumentMetadata`

```yaml
# ─── HIÉRARCHIE ORGANISATIONNELLE (configurée par l'utilisateur) ───
tenant: "acme-corp"              # Organisation / client
domain: "engineering"            # Domaine métier
subdomain: "backend"             # Sous-domaine

# ─── IDENTIFICATION DOCUMENT (détecté automatiquement + modifiable) ───
document_id: "doc_a1b2c3"       # ID unique généré
title: "Guide API REST"         # Extrait du H1 ou nom de fichier
author: "Jean Dupont"           # Extrait des métadonnées PDF/DOCX
source: "api-guide.pdf"         # Nom du fichier source
source_path: "./docs/api/"      # Chemin relatif du fichier
source_type: "pdf"              # Type de fichier (pdf, docx, md, txt, html, csv)
source_url: ""                  # URL d'origine si applicable
mime_type: "application/pdf"    # MIME type détecté

# ─── TEMPORALITÉ (détecté automatiquement) ───
created_at: "2025-06-15"        # Date de création du document
modified_at: "2026-01-20"       # Date de dernière modification
ingested_at: "2026-02-12T..."   # Timestamp d'ingestion dans RAGKIT
version: "1.0"                  # Version du document

# ─── CONTENU (détecté automatiquement) ───
language: "fr"                  # Langue détectée (ISO 639-1)
page_count: 42                  # Nombre de pages
word_count: 12500               # Nombre de mots
has_tables: true                # Contient des tableaux
has_images: true                # Contient des images
has_code: false                 # Contient des blocs de code
encoding: "utf-8"              # Encodage détecté

# ─── CLASSIFICATION (modifiable par l'utilisateur) ───
tags: ["api", "rest", "auth"]   # Tags libres
category: "technical"           # Catégorie prédéfinie
confidentiality: "internal"     # public | internal | confidential | secret
status: "published"             # draft | review | published | archived

# ─── PARSING (rempli par le système) ───
parser_engine: "unstructured"   # Moteur utilisé
ocr_applied: false              # OCR a été nécessaire
parsing_quality: 0.95           # Score de qualité du parsing (0-1)
parsing_warnings: []            # Avertissements éventuels
```

## Schéma `ChunkMetadata` (hérité + enrichi à l'Étape 2)

```yaml
# ─── HÉRITÉ DU DOCUMENT (copié automatiquement) ───
document_id: "doc_a1b2c3"
tenant: "acme-corp"
domain: "engineering"
title: "Guide API REST"
source: "api-guide.pdf"
language: "fr"
tags: ["api", "rest", "auth"]

# ─── SPÉCIFIQUE AU CHUNK (généré par le chunker) ───
chunk_id: "doc_a1b2c3-chunk-007"
chunk_index: 7                  # Position dans le document
total_chunks: 23                # Nombre total de chunks du document
chunk_strategy: "semantic"      # Stratégie utilisée
chunk_size_tokens: 487          # Taille en tokens
chunk_size_chars: 2134          # Taille en caractères

# ─── CONTEXTE STRUCTUREL ───
page_number: 12                 # Page d'origine
section_title: "Authentication" # Titre de section parent
heading_path: ["API", "Auth"]   # Fil d'Ariane des headings
paragraph_index: 3              # Index du paragraphe dans la section

# ─── RELATIONS ───
previous_chunk_id: "...-chunk-006"
next_chunk_id: "...-chunk-008"
parent_chunk_id: null           # Pour le parent-child chunking
```

---

# PARTIE 3 — PLAN D'IMPLÉMENTATION DÉTAILLÉ : ÉTAPE 1

# ÉTAPE 1 : INGESTION & PREPROCESSING

**Objectif** : Pipeline robuste qui transforme tout type de document en objets `Document` normalisés avec des métadonnées complètes et un texte propre.

**Branche Git** : `v2/step-01-ingestion`

---

## Phase 1.1 — Fondations (Jour 1)

### 1.1.1 Structure du projet

```
ragkit/
├── pyproject.toml
├── ragkit/
│   ├── __init__.py
│   ├── models.py              # Document, Chunk, DocumentMetadata
│   ├── config/
│   │   ├── __init__.py
│   │   ├── schema.py          # Pydantic models pour toute la config
│   │   └── defaults.py        # Valeurs par défaut
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── pipeline.py        # IngestionPipeline orchestrateur
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # BaseParser (interface)
│   │   │   ├── pdf.py         # PDFParser
│   │   │   ├── docx.py        # DocxParser
│   │   │   ├── markdown.py    # MarkdownParser
│   │   │   ├── text.py        # TextParser
│   │   │   ├── html.py        # HTMLParser
│   │   │   ├── csv_parser.py  # CSVParser
│   │   │   └── factory.py     # parser_factory(source_type) → Parser
│   │   ├── preprocessing/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py    # PreprocessingPipeline
│   │   │   ├── normalizer.py  # Unicode, casse, ponctuation
│   │   │   ├── cleaner.py     # URLs, espaces, caractères spéciaux
│   │   │   ├── language.py    # Détection de langue
│   │   │   └── dedup.py       # Déduplication (exact, fuzzy, semantic)
│   │   └── metadata/
│   │       ├── __init__.py
│   │       ├── extractor.py   # Extraction auto des métadonnées
│   │       ├── enricher.py    # Enrichissement (langue, stats, etc.)
│   │       └── schema.py      # DocumentMetadata Pydantic model
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── hashing.py         # Fingerprinting pour dedup
│   │   └── file_utils.py      # Scan répertoire, détection type
│   └── cli/
│       ├── __init__.py
│       └── ingest.py          # Commande CLI ragkit ingest
├── tests/
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_parsers/
│   │   ├── test_preprocessing/
│   │   └── test_metadata/
│   ├── integration/
│   │   └── test_ingestion_pipeline.py
│   └── fixtures/
│       ├── sample.pdf
│       ├── sample.docx
│       ├── sample.md
│       ├── sample.txt
│       ├── sample.html
│       └── sample.csv
└── ragkit.yaml                 # Config par défaut
```

### 1.1.2 Modèles de données (`ragkit/models.py`)

```python
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any
import uuid


class DocumentMetadata(BaseModel):
    """Structure de métadonnées par défaut, large et extensible."""

    # ─── HIÉRARCHIE ORGANISATIONNELLE ───
    tenant: str = "default"
    domain: str = ""
    subdomain: str = ""

    # ─── IDENTIFICATION ───
    document_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    title: str = ""
    author: str = ""
    source: str = ""               # nom de fichier
    source_path: str = ""          # chemin relatif
    source_type: str = ""          # pdf, docx, md, txt, html, csv
    source_url: str = ""
    mime_type: str = ""

    # ─── TEMPORALITÉ ───
    created_at: datetime | None = None
    modified_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"

    # ─── CONTENU (auto-détecté) ───
    language: str = ""             # ISO 639-1
    page_count: int = 0
    word_count: int = 0
    char_count: int = 0
    has_tables: bool = False
    has_images: bool = False
    has_code: bool = False
    encoding: str = "utf-8"

    # ─── CLASSIFICATION (user-editable) ───
    tags: list[str] = Field(default_factory=list)
    category: str = ""
    confidentiality: str = "internal"  # public|internal|confidential|secret
    status: str = "published"          # draft|review|published|archived

    # ─── PARSING (système) ───
    parser_engine: str = ""
    ocr_applied: bool = False
    parsing_quality: float = 1.0
    parsing_warnings: list[str] = Field(default_factory=list)

    # ─── EXTENSIBLE ───
    custom: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Document parsé avec texte brut et métadonnées."""

    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    content: str                    # texte brut extrait
    raw_content: str = ""           # contenu original avant preprocessing
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

    # Sections structurées (optionnel, pour header_detection)
    sections: list[DocumentSection] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)


class DocumentSection(BaseModel):
    """Section détectée dans le document."""
    title: str = ""
    level: int = 0                 # 0=titre principal, 1=H2, 2=H3...
    content: str = ""
    page_number: int | None = None


class TableData(BaseModel):
    """Tableau extrait du document."""
    page_number: int | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    caption: str = ""
```

### 1.1.3 Configuration (`ragkit/config/schema.py` — section ingestion)

```python
class OCRConfig(BaseModel):
    enabled: bool = False
    engine: str = "tesseract"      # tesseract | easyocr
    languages: list[str] = ["fra", "eng"]

class ParsingConfig(BaseModel):
    engine: str = "auto"           # auto | unstructured | docling | pypdf
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    table_extraction: str = "auto" # auto | preserve | markdown | separate | none
    image_captioning: bool = False
    header_detection: bool = True

class PreprocessingConfig(BaseModel):
    lowercase: bool = False
    remove_punctuation: bool = False
    normalize_unicode: str = "NFKC"  # NFC | NFD | NFKC | NFKD | none
    remove_urls: bool = False
    language_detection: bool = True
    strip_extra_whitespace: bool = True

class DeduplicationConfig(BaseModel):
    enabled: bool = False
    strategy: str = "exact"        # exact | fuzzy | semantic
    threshold: float = 0.95

class MetadataDefaultsConfig(BaseModel):
    """Valeurs par défaut injectées dans tous les documents."""
    tenant: str = "default"
    domain: str = ""
    subdomain: str = ""
    confidentiality: str = "internal"
    tags: list[str] = Field(default_factory=list)

class SourceConfig(BaseModel):
    type: str = "local"
    path: str = "./data/documents"
    patterns: list[str] = ["*.pdf", "*.docx", "*.md", "*.txt"]
    recursive: bool = True

class IngestionConfig(BaseModel):
    sources: list[SourceConfig] = Field(default_factory=lambda: [SourceConfig()])
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    metadata_defaults: MetadataDefaultsConfig = Field(default_factory=MetadataDefaultsConfig)
```

**Critère de validation Phase 1.1** :
- `pytest tests/unit/test_models.py` → tous les modèles Pydantic valident et sérialisent

---

## Phase 1.2 — Parsers (Jours 2-3)

### 1.2.1 Interface de base

```python
# ragkit/ingestion/parsers/base.py
from abc import ABC, abstractmethod
from ragkit.models import Document, DocumentMetadata

class BaseParser(ABC):
    """Interface commune pour tous les parsers."""

    @abstractmethod
    def parse(self, file_path: str, metadata: DocumentMetadata) -> Document:
        """Parse un fichier et retourne un Document."""
        ...

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """Retourne True si ce parser supporte l'extension."""
        ...
```

### 1.2.2 Parsers à implémenter

| Parser | Fichier | Lib principale | Auto-détection métadonnées |
|--------|---------|---------------|--------------------------|
| `PDFParser` | `pdf.py` | `pypdf` + `unstructured` | title (metadata PDF), author, created_at, page_count, has_images, has_tables |
| `DocxParser` | `docx.py` | `python-docx` | title, author, created_at, modified_at, word_count, has_tables, has_images |
| `MarkdownParser` | `markdown.py` | `markdown-it-py` | title (premier H1), headings structure, has_code |
| `TextParser` | `text.py` | stdlib | encoding detection, word_count |
| `HTMLParser` | `html.py` | `beautifulsoup4` | title (tag `<title>`), language (tag `<html lang>`), has_tables |
| `CSVParser` | `csv_parser.py` | `pandas` | column names, row_count, détection séparateur |

### 1.2.3 Factory

```python
# ragkit/ingestion/parsers/factory.py
PARSER_MAP = {
    ".pdf": PDFParser,
    ".docx": DocxParser,
    ".doc": DocxParser,       # conversion .doc → .docx via LibreOffice
    ".md": MarkdownParser,
    ".txt": TextParser,
    ".html": HTMLParser,
    ".htm": HTMLParser,
    ".csv": CSVParser,
}

def create_parser(file_path: str, config: ParsingConfig) -> BaseParser:
    ext = Path(file_path).suffix.lower()
    parser_class = PARSER_MAP.get(ext)
    if not parser_class:
        raise UnsupportedFormatError(f"Format {ext} non supporté")
    return parser_class(config)
```

### 1.2.4 OCR intégré dans PDFParser

```python
# Dans pdf.py
class PDFParser(BaseParser):
    def parse(self, file_path, metadata):
        doc = self._extract_text(file_path)

        # Si le texte est trop court vs nombre de pages → probablement scanné
        if self._needs_ocr(doc, file_path):
            if self.config.ocr.enabled:
                doc = self._apply_ocr(file_path)
                metadata.ocr_applied = True
            else:
                metadata.parsing_warnings.append("Document semble scanné mais OCR désactivé")

        return doc
```

**Critère de validation Phase 1.2** :
- Chaque parser testé avec un fichier fixture
- `pytest tests/unit/test_parsers/` → 100% pass
- Métadonnées auto-détectées correctement pour chaque format

---

## Phase 1.3 — Metadata Extractor & Enricher (Jour 4)

### 1.3.1 Extraction automatique

```python
# ragkit/ingestion/metadata/extractor.py
class MetadataExtractor:
    """Extrait les métadonnées depuis le fichier source."""

    def extract(self, file_path: str) -> DocumentMetadata:
        metadata = DocumentMetadata()

        # Infos fichier système
        path = Path(file_path)
        stat = path.stat()
        metadata.source = path.name
        metadata.source_path = str(path.parent)
        metadata.source_type = path.suffix.lstrip(".").lower()
        metadata.mime_type = mimetypes.guess_type(file_path)[0] or ""
        metadata.modified_at = datetime.fromtimestamp(stat.st_mtime)
        metadata.created_at = datetime.fromtimestamp(stat.st_ctime)

        return metadata
```

### 1.3.2 Enrichissement post-parsing

```python
# ragkit/ingestion/metadata/enricher.py
class MetadataEnricher:
    """Enrichit les métadonnées après parsing du contenu."""

    def __init__(self, config: PreprocessingConfig):
        self.config = config

    def enrich(self, doc: Document) -> Document:
        meta = doc.metadata

        # Statistiques de contenu
        meta.word_count = len(doc.content.split())
        meta.char_count = len(doc.content)

        # Détection de langue
        if self.config.language_detection and doc.content:
            meta.language = detect_language(doc.content)

        # Détection de contenu spécial
        meta.has_code = self._detect_code(doc.content)
        meta.has_tables = len(doc.tables) > 0

        # Titre fallback : premier heading ou nom de fichier
        if not meta.title:
            meta.title = self._extract_title(doc) or meta.source

        # Score qualité
        meta.parsing_quality = self._compute_quality_score(doc)

        return doc
```

### 1.3.3 Application des defaults utilisateur

```python
# ragkit/ingestion/metadata/enricher.py
    def apply_defaults(self, doc: Document, defaults: MetadataDefaultsConfig) -> Document:
        """Applique les valeurs par défaut de l'utilisateur."""
        if defaults.tenant:
            doc.metadata.tenant = defaults.tenant
        if defaults.domain:
            doc.metadata.domain = defaults.domain
        if defaults.subdomain:
            doc.metadata.subdomain = defaults.subdomain
        if defaults.tags:
            doc.metadata.tags = list(set(doc.metadata.tags + defaults.tags))
        if defaults.confidentiality:
            doc.metadata.confidentiality = defaults.confidentiality
        return doc
```

**Critère de validation Phase 1.3** :
- Un PDF de test → métadonnées complètes auto-détectées (title, author, language, page_count, etc.)
- Les defaults utilisateur s'appliquent correctement
- `pytest tests/unit/test_metadata/` → pass

---

## Phase 1.4 — Preprocessing Pipeline (Jour 5)

### 1.4.1 Normalizer

```python
# ragkit/ingestion/preprocessing/normalizer.py
import unicodedata, re

class TextNormalizer:
    def __init__(self, config: PreprocessingConfig):
        self.config = config

    def normalize(self, text: str) -> str:
        # 1. Unicode normalization
        if self.config.normalize_unicode != "none":
            text = unicodedata.normalize(self.config.normalize_unicode, text)

        # 2. Extra whitespace
        if self.config.strip_extra_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
            text = re.sub(r'\n{3,}', '\n\n', text)

        # 3. URLs
        if self.config.remove_urls:
            text = re.sub(r'https?://\S+', '', text)

        # 4. Lowercase (optionnel — attention, désactivé par défaut)
        if self.config.lowercase:
            text = text.lower()

        # 5. Ponctuation
        if self.config.remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)

        return text
```

### 1.4.2 Deduplication

```python
# ragkit/ingestion/preprocessing/dedup.py
import hashlib

class Deduplicator:
    def __init__(self, config: DeduplicationConfig):
        self.config = config
        self._seen_hashes: set[str] = set()

    def is_duplicate(self, doc: Document) -> bool:
        if not self.config.enabled:
            return False

        if self.config.strategy == "exact":
            h = hashlib.sha256(doc.content.encode()).hexdigest()
            if h in self._seen_hashes:
                return True
            self._seen_hashes.add(h)
            return False

        elif self.config.strategy == "fuzzy":
            # MinHash / SimHash pour near-duplicates
            return self._fuzzy_check(doc)

        return False
```

### 1.4.3 Pipeline complet

```python
# ragkit/ingestion/preprocessing/pipeline.py
class PreprocessingPipeline:
    def __init__(self, config: PreprocessingConfig):
        self.normalizer = TextNormalizer(config)

    def process(self, doc: Document) -> Document:
        """Applique toutes les étapes de preprocessing."""
        doc.raw_content = doc.content  # sauvegarde de l'original
        doc.content = self.normalizer.normalize(doc.content)
        return doc
```

**Critère de validation Phase 1.4** :
- Texte avec caractères Unicode bizarres → normalisé proprement
- Document en double → détecté comme duplicate
- `pytest tests/unit/test_preprocessing/` → pass

---

## Phase 1.5 — Orchestrateur & CLI (Jour 6)

### 1.5.1 IngestionPipeline

```python
# ragkit/ingestion/pipeline.py
class IngestionPipeline:
    def __init__(self, config: IngestionConfig):
        self.config = config
        self.preprocessor = PreprocessingPipeline(config.preprocessing)
        self.metadata_extractor = MetadataExtractor()
        self.metadata_enricher = MetadataEnricher(config.preprocessing)
        self.deduplicator = Deduplicator(config.deduplication)

    def ingest(self, source_path: str) -> list[Document]:
        """Pipeline complet : scan → parse → metadata → preprocess → dedup."""
        documents = []
        files = scan_directory(source_path, self.config.sources[0].patterns,
                               self.config.sources[0].recursive)

        for file_path in files:
            try:
                # 1. Extraction métadonnées fichier
                metadata = self.metadata_extractor.extract(file_path)

                # 2. Application des defaults utilisateur
                self.metadata_enricher.apply_defaults(metadata, self.config.metadata_defaults)

                # 3. Parsing
                parser = create_parser(file_path, self.config.parsing)
                doc = parser.parse(file_path, metadata)
                doc.metadata.parser_engine = parser.__class__.__name__

                # 4. Enrichissement métadonnées post-parsing
                doc = self.metadata_enricher.enrich(doc)

                # 5. Preprocessing texte
                doc = self.preprocessor.process(doc)

                # 6. Déduplication
                if self.deduplicator.is_duplicate(doc):
                    logger.info(f"Duplicate détecté, ignoré: {file_path}")
                    continue

                documents.append(doc)
                logger.info(f"Ingéré: {file_path} → {doc.metadata.word_count} mots, "
                           f"lang={doc.metadata.language}")

            except Exception as e:
                logger.error(f"Erreur ingestion {file_path}: {e}")

        return documents
```

### 1.5.2 CLI

```python
# ragkit/cli/ingest.py
import click

@click.command()
@click.argument("path", default="./data/documents")
@click.option("--config", "-c", default="ragkit.yaml")
@click.option("--show-metadata", is_flag=True)
@click.option("--dry-run", is_flag=True)
def ingest(path, config, show_metadata, dry_run):
    """Ingère les documents depuis un dossier."""
    cfg = load_config(config)
    pipeline = IngestionPipeline(cfg.ingestion)
    documents = pipeline.ingest(path)

    click.echo(f"\n{'='*60}")
    click.echo(f"  Ingestion terminée : {len(documents)} documents")
    click.echo(f"{'='*60}")

    for doc in documents:
        m = doc.metadata
        click.echo(f"\n  📄 {m.source}")
        click.echo(f"     Titre    : {m.title}")
        click.echo(f"     Langue   : {m.language}")
        click.echo(f"     Mots     : {m.word_count}")
        click.echo(f"     Pages    : {m.page_count}")
        click.echo(f"     Qualité  : {m.parsing_quality:.0%}")
        if show_metadata:
            click.echo(f"     Metadata : {m.model_dump_json(indent=2)}")

    if not dry_run:
        # Sauvegarder les documents pour l'Étape 2
        save_documents(documents, cfg.data_dir / "ingested")
```

**Critère de validation Phase 1.5** :
- `ragkit ingest ./tests/fixtures/ --show-metadata` → affiche les 6 documents de test avec métadonnées complètes
- Chaque format (PDF, DOCX, MD, TXT, HTML, CSV) parsé correctement
- Les métadonnées auto-détectées sont exactes

---

## Phase 1.6 — Tests d'intégration & Validation finale (Jour 7)

### Tests à écrire

```python
# tests/integration/test_ingestion_pipeline.py

class TestIngestionPipeline:
    def test_full_pipeline_mixed_formats(self, fixtures_dir):
        """Ingère un dossier avec tous les formats supportés."""
        config = IngestionConfig(
            sources=[SourceConfig(path=str(fixtures_dir))],
            metadata_defaults=MetadataDefaultsConfig(
                tenant="test-corp", domain="engineering"
            ),
        )
        pipeline = IngestionPipeline(config)
        docs = pipeline.ingest(str(fixtures_dir))

        assert len(docs) >= 5  # au moins les 5 formats principaux
        for doc in docs:
            assert doc.metadata.tenant == "test-corp"
            assert doc.metadata.domain == "engineering"
            assert doc.metadata.language != ""
            assert doc.metadata.word_count > 0
            assert doc.metadata.source != ""

    def test_metadata_auto_detection_pdf(self, sample_pdf):
        """Les métadonnées PDF sont extraites automatiquement."""
        ...

    def test_deduplication_exact(self, fixtures_dir):
        """Les documents identiques sont détectés."""
        ...

    def test_preprocessing_unicode(self):
        """La normalisation Unicode fonctionne."""
        ...

    def test_ocr_fallback(self, scanned_pdf):
        """L'OCR se déclenche sur un PDF scanné."""
        ...

    def test_metadata_defaults_applied(self):
        """Les defaults utilisateur sont injectés."""
        ...
```

### Checklist de validation finale Étape 1

```
□ ragkit ingest ./docs → parse tous les formats sans erreur
□ Métadonnées auto-détectées : title, author, language, page_count, word_count
□ Métadonnées par défaut (tenant, domain) appliquées
□ OCR se déclenche sur PDF scanné quand activé
□ Déduplication fonctionne (exact)
□ Preprocessing : unicode normalisé, whitespace nettoyé
□ CLI affiche un résumé clair
□ Documents sérialisés sur disque pour l'Étape 2
□ pytest → 100% pass (unit + integration)
□ Aucune dépendance sur les étapes suivantes (embedding, vectorstore, etc.)
```

---

## Dépendances Python (Étape 1 uniquement)

```toml
[project]
dependencies = [
    "pydantic>=2.0",
    "click>=8.0",
    "pypdf>=4.0",
    "python-docx>=1.0",
    "beautifulsoup4>=4.12",
    "markdown-it-py>=3.0",
    "pandas>=2.0",
    "langdetect>=1.0.9",
    "python-magic>=0.4",        # détection MIME
    "structlog>=24.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
ocr = [
    "pytesseract>=0.3",
    "easyocr>=1.7",
]
```

---

## Récapitulatif Étape 1

| Phase | Contenu | Durée | Livrable |
|-------|---------|-------|----------|
| 1.1 | Modèles, config, structure projet | 1 jour | `models.py`, `schema.py` |
| 1.2 | 6 parsers + factory + OCR | 2 jours | Parsing de tous les formats |
| 1.3 | Metadata extractor + enricher | 1 jour | Métadonnées auto-détectées |
| 1.4 | Preprocessing (normalisation, dedup) | 1 jour | Texte propre et normalisé |
| 1.5 | Pipeline orchestrateur + CLI | 1 jour | `ragkit ingest` fonctionnel |
| 1.6 | Tests intégration + validation | 1 jour | 100% coverage, pipeline validé |
| **Total** | | **7 jours** | **Étape 1 complète et validée** |
