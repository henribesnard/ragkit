# Etape 5 : RECHERCHE SEMANTIQUE

## Objectif
Ameliorer la recherche semantique avec MMR (Maximum Marginal Relevance), query expansion, et exposer les parametres dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| SemanticRetriever | `ragkit/retrieval/semantic.py` | `retrieve(query)` avec vector_store.search + threshold filtering |
| SemanticRetrievalConfig | `ragkit/config/schema.py` | enabled, weight, top_k, similarity_threshold |
| RetrievalConfigV2 | `ragkit/config/schema_v2.py` | mmr_enabled, mmr_lambda, diversity_threshold, query_expansion, multi_query_strategy - NON branche |
| UI | `Settings.tsx` | top_k, semantic_weight |

### Ce qui manque
- MMR (Maximum Marginal Relevance) pour diversifier les resultats
- Query expansion (synonymes, reformulation LLM)
- Multi-query strategies (single, multi_perspective, HyDE)
- Filtrage par metadata dans la recherche semantique
- Exposition MMR et query_expansion dans l'UI

---

## Phase 2 : Implementation MMR

### 2.1 Modifier `ragkit/retrieval/semantic.py`

```python
class SemanticRetriever:
    def __init__(self, vector_store, embedder, config):
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = config.top_k
        self.threshold = config.similarity_threshold
        self.mmr_enabled = getattr(config, 'mmr_enabled', False)
        self.mmr_lambda = getattr(config, 'mmr_lambda', 0.5)

    async def retrieve(self, query: str, filters: dict | None = None) -> list[RetrievalResult]:
        query_embedding = await self.embedder.embed_query(query)

        # Recuperer plus de candidats si MMR active
        fetch_k = self.top_k * 3 if self.mmr_enabled else self.top_k
        results = await self.vector_store.search(query_embedding, fetch_k, filters=filters)

        filtered = [r for r in results if r.score >= self.threshold]

        if self.mmr_enabled and len(filtered) > self.top_k:
            filtered = self._apply_mmr(query_embedding, filtered, self.top_k)

        return [RetrievalResult(chunk=r.chunk, score=r.score, retrieval_type="semantic") for r in filtered]

    def _apply_mmr(self, query_emb, results, top_k):
        """Maximum Marginal Relevance selection."""
        # Selectionne iterativement les documents les plus pertinents
        # tout en penalisant la similarite avec les documents deja selectionnes
```

### 2.2 Creer `ragkit/retrieval/mmr.py`

```python
def mmr_select(
    query_embedding: list[float],
    candidate_embeddings: list[list[float]],
    scores: list[float],
    top_k: int,
    lambda_param: float = 0.5,
) -> list[int]:
    """Selectionne les top_k indices via MMR."""
```

---

## Phase 3 : Query Expansion

### 3.1 Creer `ragkit/retrieval/query_expansion.py`

```python
class QueryExpander:
    """Expansion de requete pour ameliorer le recall."""

    def __init__(self, strategy: str = "none", llm=None):
        self.strategy = strategy
        self.llm = llm

    async def expand(self, query: str) -> list[str]:
        if self.strategy == "none":
            return [query]
        elif self.strategy == "synonyms":
            return self._synonym_expansion(query)
        elif self.strategy == "llm_rewrite":
            return await self._llm_rewrite(query)

    def _synonym_expansion(self, query: str) -> list[str]:
        """Ajoute des synonymes aux termes cles."""

    async def _llm_rewrite(self, query: str) -> list[str]:
        """Demande au LLM de reformuler la requete en 2-3 variantes."""
```

### 3.2 Integrer au SemanticRetriever

Si query_expansion est active, generer les variantes de la requete et fusionner les resultats.

---

## Phase 4 : UI - Exposition des Parametres

### Settings.tsx - Section Recherche enrichie

Ajouter dans la carte Retrieval (onglet advanced) :
- **MMR enabled** : Checkbox (defaut: false)
- **MMR Lambda** : Slider 0-1 (defaut: 0.5) - visible si MMR enabled
- **Query Expansion** : Select (none / synonyms / llm_rewrite)

---

## Phase 5 : Tests & Validation

### Tests
```
tests/unit/test_retrieval.py (enrichir)
  - test_mmr_selection
  - test_mmr_diversity
  - test_query_expansion_synonyms
  - test_semantic_retriever_with_mmr
  - test_semantic_retriever_with_filters
```

### Validation
1. Builder dans `.build/`
2. Activer MMR dans l'UI et verifier la diversite des resultats
3. Tester query expansion avec reformulation LLM
4. Verifier que le filtrage metadata fonctionne

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| MODIFIER | `ragkit/retrieval/semantic.py` |
| CREER | `ragkit/retrieval/mmr.py` |
| CREER | `ragkit/retrieval/query_expansion.py` |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_retrieval.py` |

---

## Criteres de Validation

- [ ] MMR implemente et diversifie les resultats
- [ ] Query expansion (synonymes) fonctionnelle
- [ ] Query expansion (LLM rewrite) fonctionnelle
- [ ] Filtrage metadata dans la recherche
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
