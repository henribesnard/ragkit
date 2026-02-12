# Etape 1 : INGESTION & PREPROCESSING

## Objectif
Mettre en place la structure de metadonnees enrichie (DocumentMetadata), ameliorer le parsing, ajouter le preprocessing texte, et exposer les parametres dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| RawDocument | `ragkit/ingestion/sources/base.py` | `content`, `source_path`, `file_type`, `metadata: dict` |
| ParsedDocument | `ragkit/ingestion/parsers/base.py` | `content`, `metadata: dict`, `structure: list[DocumentSection]` |
| DocumentSection | `ragkit/ingestion/parsers/base.py` | `title`, `level`, `content`, `metadata: dict` |
| ParsingConfig | `ragkit/config/schema.py` | `engine` (auto/unstructured/docling/pypdf), `ocr` (enabled/engine/languages) |
| DocumentParsingConfig v2 | `ragkit/config/schema_v2.py` | Complet (OCR, tables, images, headers, PDF) - NON branche |
| TextPreprocessingConfig v2 | `ragkit/config/schema_v2.py` | Complet (unicode, dedup, regex, stopwords) - NON branche |
| MetadataConfig | `ragkit/config/schema.py` | `extract: list[str]`, `custom: dict` - Minimaliste |
| Parsers | `ragkit/ingestion/parsers/` | `text.py`, `markdown.py` - Basiques |
| Source loader | `ragkit/ingestion/sources/local.py` | Charge fichiers locaux |

### Ce qui manque
- Structure de metadonnees enrichie (DocumentMetadata Pydantic model)
- Auto-detection des metadonnees (title, author, language, page_count, word_count)
- Preprocessing texte (normalisation unicode, suppression URLs, whitespace)
- Deduplication a l'ingestion (exact + fuzzy)
- Detection de langue
- Branchement de `DocumentParsingConfig` v2 au runtime
- Branchement de `TextPreprocessingConfig` v2 au runtime
- Exposition OCR/preprocessing dans l'UI

---

## Phase 2 : Implementation du Modele DocumentMetadata

### 2.1 Creer `ragkit/ingestion/metadata.py`

```python
class DocumentMetadata(BaseModel):
    # Hierarchie organisationnelle
    tenant: str = "default"
    domain: str = "general"
    subdomain: str | None = None

    # Identification document
    document_id: str  # UUID genere
    title: str | None = None  # Extrait du H1 ou nom de fichier
    author: str | None = None  # Extrait des metadonnees PDF/DOCX
    source: str  # Nom du fichier
    source_path: str  # Chemin relatif
    source_type: str  # pdf, docx, md, txt, html, csv
    source_url: str | None = None
    mime_type: str | None = None

    # Temporalite
    created_at: datetime | None = None
    modified_at: datetime | None = None
    ingested_at: datetime  # Timestamp d'ingestion
    version: str = "1.0"

    # Contenu (auto-detecte)
    language: str | None = None  # ISO 639-1
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None
    has_tables: bool = False
    has_images: bool = False
    has_code: bool = False
    encoding: str = "utf-8"

    # Classification (modifiable par l'utilisateur)
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    confidentiality: Literal["public", "internal", "confidential", "secret"] = "internal"
    status: Literal["draft", "review", "published", "archived"] = "published"

    # Parsing (systeme)
    parser_engine: str | None = None
    ocr_applied: bool = False
    parsing_quality: float | None = None  # Score 0-1
    parsing_warnings: list[str] = Field(default_factory=list)

    # Extensible
    custom: dict[str, Any] = Field(default_factory=dict)
```

### 2.2 Creer `ragkit/ingestion/metadata_extractor.py`

Service d'auto-detection des metadonnees :

```python
class MetadataExtractor:
    """Extrait automatiquement les metadonnees d'un document."""

    def extract(self, raw_doc: RawDocument, parsed_doc: ParsedDocument) -> DocumentMetadata:
        """Construit DocumentMetadata a partir du document brut et parse."""

    def _detect_title(self, parsed_doc: ParsedDocument, raw_doc: RawDocument) -> str | None:
        """Extrait le titre du H1 ou du nom de fichier."""

    def _detect_author(self, raw_doc: RawDocument) -> str | None:
        """Extrait l'auteur des metadonnees PDF/DOCX."""

    def _detect_language(self, text: str) -> str | None:
        """Detecte la langue avec langdetect/fasttext."""

    def _count_content(self, text: str) -> dict:
        """word_count, char_count, has_tables, has_images, has_code."""

    def _detect_mime_type(self, source_path: str) -> str | None:
        """Detecte le MIME type."""
```

### 2.3 Modifier `ragkit/models.py`

Ajouter un champ `structured_metadata` optionnel au modele Document :

```python
class Document(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    structured_metadata: DocumentMetadata | None = None
    embedding: list[float] | None = None
```

---

## Phase 3 : Preprocessing Texte

### 3.1 Creer `ragkit/ingestion/preprocessing.py`

```python
class TextPreprocessor:
    """Pipeline de preprocessing configurable."""

    def __init__(self, config: TextPreprocessingConfig):
        self.config = config

    def process(self, text: str) -> str:
        if self.config.normalize_unicode != "none":
            text = unicodedata.normalize(self.config.normalize_unicode, text)
        if self.config.remove_urls:
            text = re.sub(r'https?://\S+', '', text)
        if self.config.remove_emails:
            text = re.sub(r'\S+@\S+\.\S+', '', text)
        if self.config.normalize_whitespace:
            text = re.sub(r'[ \t]+', ' ', text)
        if self.config.remove_extra_newlines:
            text = re.sub(r'\n{3,}', '\n\n', text)
        if self.config.remove_control_characters:
            text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C' or c in '\n\t')
        if self.config.fix_encoding_errors:
            text = text.encode('utf-8', errors='replace').decode('utf-8')
        return text.strip()
```

### 3.2 Creer `ragkit/ingestion/deduplication.py`

```python
class DocumentDeduplicator:
    """Deduplication a l'ingestion."""

    def __init__(self, strategy: str = "exact", threshold: float = 0.95):
        self.strategy = strategy
        self.threshold = threshold
        self._hashes: set[str] = set()

    def is_duplicate(self, content: str) -> bool:
        """Verifie si le document est un doublon."""

    def _exact_hash(self, content: str) -> str:
        """Hash SHA-256 du contenu."""

    def _fuzzy_hash(self, content: str) -> str:
        """SimHash ou MinHash pour deduplication fuzzy."""
```

---

## Phase 4 : Branchement de la Config v2

### 4.1 Modifier le pipeline d'ingestion

Brancher `DocumentParsingConfig` et `TextPreprocessingConfig` de `schema_v2.py` au lieu de `ParsingConfig` de `schema.py` :

- Fichier cible : `ragkit/ingestion/pipeline.py` (a creer ou modifier selon l'existant)
- Le pipeline doit : parse -> extract metadata -> preprocess -> return ParsedDocument enrichi

### 4.2 Migration douce

Garder la compatibilite avec `schema.py` via un adaptateur :
```python
def v1_to_v2_parsing_config(v1: ParsingConfig) -> DocumentParsingConfig:
    """Convertit la config v1 en v2 pour le pipeline."""
```

---

## Phase 5 : UI - Exposition des Parametres

### 5.1 Settings.tsx - Nouvelle section "Ingestion & Preprocessing"

Ajouter dans l'onglet "advanced" une carte pour :
- **Document Parsing** : engine, OCR (enable/disable, language, engine)
- **Text Preprocessing** : normalize_unicode, remove_urls, remove_emails, normalize_whitespace
- **Deduplication** : strategy (none/exact/fuzzy), threshold
- **Language Detection** : enable/disable, detector (langdetect/fasttext)

### 5.2 IPC & Commands

Ajouter les champs dans :
- `desktop/src/lib/ipc.ts` : interface Settings
- `desktop/src-tauri/src/commands.rs` : struct Settings
- Backend API : routes de configuration

### 5.3 Metadonnees par defaut configurables

Ajouter dans l'UI une section pour configurer les metadonnees par defaut :
- Tenant par defaut
- Domain par defaut
- Tags par defaut
- Confidentiality par defaut

---

## Phase 6 : Tests & Validation

### Tests unitaires
```
tests/unit/test_metadata.py
  - test_document_metadata_creation
  - test_metadata_extraction_from_pdf
  - test_metadata_extraction_from_markdown
  - test_title_detection
  - test_language_detection
  - test_content_counting

tests/unit/test_preprocessing.py
  - test_unicode_normalization
  - test_url_removal
  - test_whitespace_normalization
  - test_encoding_fix
  - test_full_pipeline

tests/unit/test_deduplication.py
  - test_exact_deduplication
  - test_fuzzy_deduplication
  - test_non_duplicate
```

### Tests d'integration
```
tests/integration/test_ingestion_pipeline.py
  - test_full_ingestion_with_metadata
  - test_ingestion_with_preprocessing
  - test_ingestion_deduplication
```

### Validation
1. Builder : `npm run tauri build` dans `.build/`
2. Verifier : les metadonnees sont visibles dans les logs d'ingestion
3. Verifier : les parametres d'ingestion apparaissent dans Settings > Advanced
4. Verifier : le preprocessing fonctionne (tester avec un doc contenant des URLs)

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/ingestion/metadata.py` |
| CREER | `ragkit/ingestion/metadata_extractor.py` |
| CREER | `ragkit/ingestion/preprocessing.py` |
| CREER | `ragkit/ingestion/deduplication.py` |
| MODIFIER | `ragkit/models.py` |
| MODIFIER | `ragkit/ingestion/parsers/base.py` |
| MODIFIER | `ragkit/ingestion/sources/local.py` |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| CREER | `tests/unit/test_metadata.py` |
| CREER | `tests/unit/test_preprocessing.py` |
| CREER | `tests/unit/test_deduplication.py` |
| CREER | `tests/integration/test_ingestion_pipeline.py` |

---

## Criteres de Validation (Definition of Done)

- [ ] DocumentMetadata model cree et fonctionnel
- [ ] Auto-detection des metadonnees (title, author, language, word_count)
- [ ] Preprocessing texte (unicode, URLs, whitespace) fonctionnel
- [ ] Deduplication (exact au minimum) fonctionnelle
- [ ] Config v2 parsing/preprocessing branchee au runtime
- [ ] Parametres exposes dans l'UI Settings
- [ ] Tests unitaires passent
- [ ] Tests d'integration passent
- [ ] Build dans `.build/` reussit
- [ ] Application installee et testee manuellement
