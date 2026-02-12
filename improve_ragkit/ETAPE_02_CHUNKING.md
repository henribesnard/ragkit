# Etape 2 : CHUNKING

## Objectif
Enrichir les strategies de chunking existantes, implementer ChunkMetadata structuree, ajouter les strategies manquantes, et exposer tous les parametres dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| BaseChunker | `ragkit/ingestion/chunkers/base.py` | `chunk()` sync + `chunk_async()` |
| FixedChunker | `ragkit/ingestion/chunkers/fixed.py` | Fonctionnel, utilise tiktoken |
| SemanticChunker | `ragkit/ingestion/chunkers/semantic.py` | Present mais methode sync potentiellement cassee |
| RecursiveChunker | `ragkit/ingestion/chunkers/recursive.py` | Present |
| SlidingWindowChunker | `ragkit/ingestion/chunkers/sliding_window.py` | Present |
| ParentChildChunker | `ragkit/ingestion/chunkers/parent_child.py` | Present |
| ChunkerFactory | `ragkit/ingestion/chunkers/factory.py` | Branche sur `ChunkingConfigV2` |
| ChunkingConfig v1 | `ragkit/config/schema.py` | `strategy: fixed/semantic`, `fixed`, `semantic` |
| ChunkingConfigV2 | `ragkit/config/schema_v2.py` | Complet (8 strategies, min/max, separateurs, parent-child) |
| Chunk model | `ragkit/models.py` | `id, document_id, content, metadata: dict, embedding` |
| UI Chunking | `desktop/src/pages/Settings.tsx` | Strategy (fixed/semantic), chunk_size, chunk_overlap |

### Ce qui manque
- ChunkMetadata model structure (au lieu de dict generique)
- sentence_based chunker (actuellement delegue a sliding_window)
- paragraph_based chunker (actuellement delegue a recursive)
- markdown_header chunker (leve NotImplementedError)
- min_chunk_size / max_chunk_size non branches dans FixedChunker
- Enrichissement des metadonnees chunk (page_number, section_title, heading_path, relations prev/next)
- Inclusion du titre du document dans chaque chunk
- UI ne propose que fixed/semantic (manque recursive, parent_child, sliding_window)

---

## Phase 2 : Implementation du Modele ChunkMetadata

### 2.1 Creer `ragkit/ingestion/chunk_metadata.py`

```python
class ChunkMetadata(BaseModel):
    # Herite du document
    document_id: str
    tenant: str = "default"
    domain: str = "general"
    title: str | None = None
    source: str | None = None
    language: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Specifique au chunk
    chunk_id: str
    chunk_index: int
    total_chunks: int | None = None
    chunk_strategy: str  # fixed / semantic / recursive / etc.
    chunk_size_tokens: int | None = None
    chunk_size_chars: int | None = None

    # Contexte structurel
    page_number: int | None = None
    section_title: str | None = None
    heading_path: list[str] = Field(default_factory=list)  # ["H1", "H2", "H3"]
    paragraph_index: int | None = None

    # Relations
    previous_chunk_id: str | None = None
    next_chunk_id: str | None = None
    parent_chunk_id: str | None = None  # Pour parent-child chunking

    # Extensible
    custom: dict[str, Any] = Field(default_factory=dict)
```

### 2.2 Modifier `ragkit/models.py` - Enrichir Chunk

```python
class Chunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    structured_metadata: ChunkMetadata | None = None
    embedding: list[float] | None = None
```

---

## Phase 3 : Amelioration des Chunkers Existants

### 3.1 FixedChunker - Ajouter min/max

Modifier `ragkit/ingestion/chunkers/fixed.py` :
- Ajouter `min_chunk_size` et `max_chunk_size` comme parametres
- Merger les chunks trop courts
- Splitter les chunks trop longs
- Remplir ChunkMetadata (chunk_strategy="fixed", chunk_size_tokens, chunk_size_chars)
- Ajouter les relations prev/next entre chunks

### 3.2 SemanticChunker - Corriger methode sync

Verifier `ragkit/ingestion/chunkers/semantic.py` :
- S'assurer que `chunk()` (sync) fonctionne correctement
- Remplir ChunkMetadata avec chunk_strategy="semantic"

### 3.3 ParentChildChunker - Enrichir metadata

Modifier `ragkit/ingestion/chunkers/parent_child.py` :
- Ajouter `parent_chunk_id` dans ChunkMetadata des enfants
- Stocker la reference vers les chunks parents

### 3.4 Tous les chunkers - Enrichissement commun

Pour chaque chunker, enrichir les chunks avec :
- `title` du document (si disponible dans ParsedDocument.metadata)
- `total_chunks` (nombre total de chunks produits)
- `chunk_size_tokens` et `chunk_size_chars`
- Relations `previous_chunk_id` / `next_chunk_id`

---

## Phase 4 : Strategies Manquantes

### 4.1 SentenceChunker (`ragkit/ingestion/chunkers/sentence.py`)

```python
class SentenceChunker(BaseChunker):
    """Decoupe par phrases completes avec fenetre configurable."""

    def __init__(self, window_size: int = 3, stride: int = 1):
        # Utilise nltk.sent_tokenize ou regex pour decoupe en phrases
        # Regroupe par fenetre de N phrases
```

### 4.2 ParagraphChunker (`ragkit/ingestion/chunkers/paragraph.py`)

```python
class ParagraphChunker(BaseChunker):
    """Decoupe par paragraphes avec merging de paragraphes courts."""

    def __init__(self, min_paragraph_size: int = 50, max_paragraph_size: int = 2000):
        # Split sur "\n\n"
        # Merge les paragraphes trop courts
        # Split les paragraphes trop longs
```

### 4.3 MarkdownHeaderChunker (`ragkit/ingestion/chunkers/markdown_header.py`)

```python
class MarkdownHeaderChunker(BaseChunker):
    """Decoupe selon la hierarchie des headers Markdown."""

    def __init__(self, headers_to_split_on: list[tuple[str, str]]):
        # Split selon #, ##, ###
        # Remplit heading_path dans ChunkMetadata
```

### 4.4 Mettre a jour ChunkerFactory

Modifier `ragkit/ingestion/chunkers/factory.py` :
- Remplacer les TODO pour sentence_based, paragraph_based, markdown_header
- Brancher les nouvelles implementations

---

## Phase 5 : UI - Exposition des Parametres

### 5.1 Settings.tsx - Enrichir la section Chunking

Dans l'onglet "advanced", ajouter :
- **Strategy** : Etendre les options (fixed, semantic, recursive, parent_child, sliding_window, sentence_based, paragraph_based, markdown_header)
- **Parametres de taille** : chunk_size, chunk_overlap, min_chunk_size, max_chunk_size
- **Separateurs** (pour recursive) : liste editable
- **Parent-child** (si strategy=parent_child) : parent_chunk_size, child_chunk_size
- **Metadata enrichment** : checkboxes pour add_document_title, add_section_title, add_page_number

### 5.2 IPC & Commands

Ajouter les nouveaux champs dans Settings (ipc.ts, commands.rs, backend API).

---

## Phase 6 : Tests & Validation

### Tests unitaires
```
tests/unit/test_chunkers.py (enrichir l'existant)
  - test_fixed_chunker_min_max
  - test_fixed_chunker_metadata_enrichment
  - test_sentence_chunker
  - test_paragraph_chunker
  - test_markdown_header_chunker
  - test_parent_child_metadata
  - test_chunk_relations_prev_next
  - test_chunk_metadata_structure

tests/unit/test_chunk_metadata.py
  - test_chunk_metadata_creation
  - test_chunk_metadata_from_document
  - test_heading_path
```

### Validation
1. Builder dans `.build/`
2. Ingester un document avec chaque strategie
3. Verifier les metadonnees des chunks dans les logs
4. Verifier que l'UI propose toutes les strategies
5. Verifier que les parametres de taille fonctionnent

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/ingestion/chunk_metadata.py` |
| CREER | `ragkit/ingestion/chunkers/sentence.py` |
| CREER | `ragkit/ingestion/chunkers/paragraph.py` |
| CREER | `ragkit/ingestion/chunkers/markdown_header.py` |
| MODIFIER | `ragkit/models.py` |
| MODIFIER | `ragkit/ingestion/chunkers/fixed.py` |
| MODIFIER | `ragkit/ingestion/chunkers/semantic.py` |
| MODIFIER | `ragkit/ingestion/chunkers/parent_child.py` |
| MODIFIER | `ragkit/ingestion/chunkers/factory.py` |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_chunkers.py` |
| CREER | `tests/unit/test_chunk_metadata.py` |

---

## Criteres de Validation

- [ ] ChunkMetadata model cree et fonctionnel
- [ ] Toutes les strategies de chunking fonctionnelles (8 strategies)
- [ ] min_chunk_size / max_chunk_size branches dans FixedChunker
- [ ] Relations prev/next entre chunks
- [ ] Titre du document inclus dans chaque chunk
- [ ] heading_path rempli pour markdown_header
- [ ] parent_chunk_id rempli pour parent_child
- [ ] Strategies exposees dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
