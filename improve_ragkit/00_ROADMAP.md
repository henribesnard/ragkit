# RAGKit - Roadmap d'Amelioration Incrementale

## Philosophie : "Strangler Fig Pattern"

On conserve le code existant comme base fonctionnelle. Pour chaque etape :

1. **Auditer** - Lister ce qui existe deja dans le code actuel pour ce domaine
2. **Completer** - Ajouter ce qui manque par rapport au plan
3. **Brancher** - Connecter les morceaux qui existent mais ne sont pas relies
4. **Tester & Valider** - Ecrire les tests, builder dans `.build/`, installer et valider

---

## Etat Actuel du Codebase (Audit Global)

### Backend Python (`ragkit/`)
- **Config v1** : `ragkit/config/schema.py` - Configuration actuelle en production
- **Config v2** : `ragkit/config/schema_v2.py` - Schemas exhaustifs definis mais NON branches
- **Models** : `ragkit/models.py` - Document, Chunk, RetrievalResult (metadonnees = dict generique)
- **Parsers** : `ragkit/ingestion/parsers/` - base, text, markdown (metadonnees minimales)
- **Chunkers** : `ragkit/ingestion/chunkers/` - fixed, semantic, recursive, sliding_window, parent_child, factory
- **Embedding** : `ragkit/embedding/` - base + providers (openai, ollama, cohere, litellm, onnx)
- **VectorStore** : `ragkit/vectorstore/` - base + providers (chroma, qdrant) + chromadb_adapter
- **Retrieval** : `ragkit/retrieval/` - semantic, lexical (BM25), fusion, rerank
- **LLM** : `ragkit/llm/` - module present
- **State** : `ragkit/state/` - models, store
- **API** : `ragkit/api/` - routes (health, status, admin/websocket)

### Desktop Tauri (`desktop/`)
- **Frontend React** : Settings.tsx avec onglets general/advanced/json
- **IPC** : ipc.ts communique avec Rust commands.rs qui proxie vers le backend Python
- **Parametres UI exposes** : embedding (provider/model), LLM (provider/model/temperature/max_tokens/top_p/system_prompt), chunking (strategy/size/overlap), retrieval (architecture/top_k/weights/rerank)

### Ecarts Identifies
- `schema_v2.py` definit tous les parametres exhaustifs mais n'est PAS branche au runtime
- Les metadonnees documents/chunks sont des `dict[str, Any]` sans structure definie
- L'index lexical (BM25) n'est jamais alimente dans le pipeline d'ingestion
- L'UI n'expose qu'une fraction des parametres disponibles
- Pas de cache de requetes, pas de monitoring, pas de securite

---

## Vue d'Ensemble des 13 Etapes

| # | Etape | Priorite | Complexite | Dependances |
|---|-------|----------|------------|-------------|
| 1 | Ingestion & Preprocessing | CRITIQUE | Haute | Aucune |
| 2 | Chunking | HAUTE | Moyenne | Etape 1 |
| 3 | Embedding | HAUTE | Moyenne | Etape 2 |
| 4 | Base de Donnees Vectorielle | HAUTE | Moyenne | Etape 3 |
| 5 | Recherche Semantique | HAUTE | Moyenne | Etape 4 |
| 6 | Recherche Lexicale | CRITIQUE | Haute | Etape 2 |
| 7 | Recherche Hybride (Fusion) | HAUTE | Moyenne | Etapes 5+6 |
| 8 | Reranking | MOYENNE | Moyenne | Etape 7 |
| 9 | LLM / Generation | HAUTE | Haute | Etape 8 |
| 10 | Cache & Performance | MOYENNE | Haute | Etapes 1-9 |
| 11 | Monitoring & Evaluation | MOYENNE | Moyenne | Etapes 1-9 |
| 12 | Securite & Compliance | BASSE | Haute | Etapes 1-9 |
| 13 | Mise a Jour & Maintenance | BASSE | Moyenne | Etapes 1-9 |

---

## Structure de Metadonnees Enrichie (Transversale)

L'amelioration des metadonnees est un prealable qui sera implemente a l'**Etape 1** et enrichie progressivement :

### DocumentMetadata (implemente en Etape 1)
```
Hierarchie organisationnelle : tenant, domain, subdomain
Identification : document_id, title, author, source, source_path, source_type, source_url, mime_type
Temporalite : created_at, modified_at, ingested_at, version
Contenu (auto-detecte) : language, page_count, word_count, char_count, has_tables, has_images, has_code, encoding
Classification (modifiable) : tags, category, confidentiality, status
Parsing (systeme) : parser_engine, ocr_applied, parsing_quality, parsing_warnings
Extensible : custom (dict libre)
```

### ChunkMetadata (implemente en Etape 2)
```
Herite du document : document_id, tenant, domain, title, source, language, tags
Specifique chunk : chunk_id, chunk_index, total_chunks, chunk_strategy, chunk_size_tokens, chunk_size_chars
Contexte structurel : page_number, section_title, heading_path, paragraph_index
Relations : previous_chunk_id, next_chunk_id, parent_chunk_id
```

---

## Processus de Validation par Etape

Pour chaque etape completee :

1. **Tests unitaires** : `pytest tests/unit/test_<domaine>.py`
2. **Tests d'integration** : `pytest tests/integration/test_<domaine>.py`
3. **Build local** : Builder l'application dans `C:\Users\henri\Projets\ragkit\.build`
4. **Installation** : Installer et lancer l'application
5. **Test fonctionnel** : Verifier que le domaine fonctionne dans l'UI
6. **Validation** : Confirmer que les parametres sont exposes et fonctionnels
7. **Non-regression** : Verifier que les etapes precedentes fonctionnent toujours

---

## Documents de Reference

- `parametres_rag_exhaustif.md` - Reference des parametres RAG complets
- `ragkit/config/schema_v2.py` - Schemas Pydantic v2 (cible)
- `ragkit/config/schema.py` - Schemas Pydantic v1 (actuel)
- `ISSUES_v2.0.0_TEST2.md` - Bugs connus a corriger

---

## Plan d'Implementation par Etape

Chaque etape est detaillee dans son propre document :

- [ETAPE_01_INGESTION_PREPROCESSING.md](./ETAPE_01_INGESTION_PREPROCESSING.md)
- [ETAPE_02_CHUNKING.md](./ETAPE_02_CHUNKING.md)
- [ETAPE_03_EMBEDDING.md](./ETAPE_03_EMBEDDING.md)
- [ETAPE_04_VECTORDB.md](./ETAPE_04_VECTORDB.md)
- [ETAPE_05_RECHERCHE_SEMANTIQUE.md](./ETAPE_05_RECHERCHE_SEMANTIQUE.md)
- [ETAPE_06_RECHERCHE_LEXICALE.md](./ETAPE_06_RECHERCHE_LEXICALE.md)
- [ETAPE_07_RECHERCHE_HYBRIDE.md](./ETAPE_07_RECHERCHE_HYBRIDE.md)
- [ETAPE_08_RERANKING.md](./ETAPE_08_RERANKING.md)
- [ETAPE_09_LLM_GENERATION.md](./ETAPE_09_LLM_GENERATION.md)
- [ETAPE_10_CACHE_PERFORMANCE.md](./ETAPE_10_CACHE_PERFORMANCE.md)
- [ETAPE_11_MONITORING_EVALUATION.md](./ETAPE_11_MONITORING_EVALUATION.md)
- [ETAPE_12_SECURITE_COMPLIANCE.md](./ETAPE_12_SECURITE_COMPLIANCE.md)
- [ETAPE_13_MAINTENANCE.md](./ETAPE_13_MAINTENANCE.md)
