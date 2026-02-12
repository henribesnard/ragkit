# Etape 4 : BASE DE DONNEES VECTORIELLE

## Objectif
Exposer les parametres de la base vectorielle (distance_metric, HNSW) dans l'UI, ameliorer les adaptateurs ChromaDB/Qdrant, et brancher la config v2.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| BaseVectorStore | `ragkit/vectorstore/base.py` | add, search, delete, clear, count, stats, list_documents, list_chunks |
| ChromaDB provider | `ragkit/vectorstore/providers/chroma.py` | Fonctionnel |
| ChromaDB adapter | `ragkit/vectorstore/chromadb_adapter.py` | Adaptateur supplementaire |
| Qdrant provider | `ragkit/vectorstore/providers/qdrant.py` | Fonctionnel |
| QdrantConfig | `ragkit/config/schema.py` | mode, path, url, collection, distance_metric, add_batch_size |
| ChromaConfig | `ragkit/config/schema.py` | mode, path, collection, add_batch_size |
| VectorDBConfigV2 | `ragkit/config/schema_v2.py` | Complet (HNSW, IVF, quantization, sharding, filtrage) - NON branche |
| UI | `Settings.tsx` | Aucun parametre vector store expose |

### Ce qui manque
- `distance_metric` non expose dans l'UI
- Parametres HNSW (ef_construction, ef_search, M) non exposes dans l'UI
- Branchement de `VectorDBConfigV2` au runtime
- Gestion des operations sync dans du code async (ChromaDB, Qdrant)
- Metadata indexing non configure (quels champs indexer pour le filtrage)

---

## Phase 2 : Correction des Operations Async

### 2.1 ChromaDB - Wrapping async

ChromaDB est une librairie synchrone. Les appels doivent etre wrapes dans `asyncio.to_thread()` :

```python
async def add(self, chunks: list[Chunk]) -> None:
    await asyncio.to_thread(self._add_sync, chunks)

async def search(self, query_embedding, top_k, filters=None):
    return await asyncio.to_thread(self._search_sync, query_embedding, top_k, filters)
```

### 2.2 Qdrant - Verification async

Verifier que le client Qdrant async est utilise correctement (qdrant_client.AsyncQdrantClient).

---

## Phase 3 : Branchement Config V2

### 3.1 HNSW parametres

Lors de la creation de collection, passer les parametres HNSW :

**Qdrant** :
```python
from qdrant_client.models import VectorParams, HnswConfigDiff

client.create_collection(
    collection_name=config.collection_name,
    vectors_config=VectorParams(size=dims, distance=distance),
    hnsw_config=HnswConfigDiff(
        m=config.hnsw_m,
        ef_construct=config.hnsw_ef_construction,
    ),
)
```

**ChromaDB** :
```python
# ChromaDB expose hnsw:space, hnsw:M, hnsw:construction_ef, hnsw:search_ef
collection = client.get_or_create_collection(
    name=config.collection_name,
    metadata={
        "hnsw:space": config.distance_metric,
        "hnsw:M": config.hnsw_m,
        "hnsw:construction_ef": config.hnsw_ef_construction,
        "hnsw:search_ef": config.hnsw_ef_search,
    }
)
```

### 3.2 Distance metric

Mapper la configuration vers les enums de chaque provider :
- `cosine` -> Qdrant: Distance.COSINE, ChromaDB: "cosine"
- `euclidean` -> Qdrant: Distance.EUCLID, ChromaDB: "l2"
- `dot_product` -> Qdrant: Distance.DOT, ChromaDB: "ip"

### 3.3 Metadata indexing

Configurer les champs de metadonnees a indexer pour le filtrage rapide :
```python
# Qdrant: payload index
client.create_payload_index(
    collection_name=config.collection_name,
    field_name="tenant",
    field_schema=PayloadSchemaType.KEYWORD,
)
```

---

## Phase 4 : UI - Exposition des Parametres

### 4.1 Settings.tsx - Nouvelle section "Vector Database"

Ajouter dans l'onglet "advanced" :
- **Provider** : Select (chromadb / qdrant)
- **Distance Metric** : Select (cosine / euclidean / dot_product)
- **HNSW M** : Input numerique (defaut: 16, range 4-64)
- **HNSW ef_construction** : Input numerique (defaut: 200, range 100-1000)
- **HNSW ef_search** : Input numerique (defaut: 50, range 10-500)
- **Collection name** : Input texte
- **Storage path** : Input texte (pour mode persistent)

### 4.2 IPC & Commands

Ajouter les champs :
```typescript
// ipc.ts Settings
vectordb_provider: string;
vectordb_distance_metric: string;
vectordb_hnsw_m: number;
vectordb_hnsw_ef_construction: number;
vectordb_hnsw_ef_search: number;
```

---

## Phase 5 : Tests & Validation

### Tests
```
tests/unit/test_vectorstore.py (enrichir)
  - test_chroma_async_wrapping
  - test_qdrant_hnsw_config
  - test_distance_metric_mapping
  - test_metadata_indexing

tests/integration/test_vectorstore.py (enrichir)
  - test_chroma_with_hnsw_params
  - test_qdrant_with_hnsw_params
  - test_search_with_metadata_filter
```

### Validation
1. Builder dans `.build/`
2. Changer la distance metric dans l'UI et re-ingester
3. Verifier que les parametres HNSW sont appliques
4. Verifier le filtrage par metadata

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| MODIFIER | `ragkit/vectorstore/providers/chroma.py` (async wrapping, HNSW) |
| MODIFIER | `ragkit/vectorstore/providers/qdrant.py` (HNSW, metadata index) |
| MODIFIER | `ragkit/vectorstore/chromadb_adapter.py` |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/integration/test_vectorstore.py` |

---

## Criteres de Validation

- [ ] Operations async correctes (ChromaDB wrape dans to_thread)
- [ ] distance_metric configurable et applique
- [ ] Parametres HNSW branches et fonctionnels
- [ ] Metadata indexing configure
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
