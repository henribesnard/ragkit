# Etape 8 : RERANKING

## Objectif
Ajouter un reranker local (cross-encoder), implementer le reranking multi-etapes, et exposer les parametres dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| BaseReranker | `ragkit/retrieval/rerank.py` | Interface abstraite |
| NoOpReranker | `ragkit/retrieval/rerank.py` | Filtre par relevance_threshold + top_n |
| CohereReranker | `ragkit/retrieval/rerank.py` | Fonctionnel via API Cohere |
| create_reranker() | `ragkit/retrieval/rerank.py` | Factory: none -> NoOp, cohere -> Cohere |
| RerankConfig | `ragkit/config/schema.py` | enabled, provider (cohere/none), model, top_n, candidates, relevance_threshold |
| RerankingConfigV2 | `ragkit/config/schema_v2.py` | Cross-encoders locaux, multi-stage, GPU, batch_size - NON branche |
| UI | `Settings.tsx` | rerank_enabled (checkbox), rerank_provider (none/cohere) |

### Ce qui manque
- Reranker local cross-encoder (ms-marco-MiniLM, bge-reranker, etc.)
- Reranking multi-etapes (stage 1: modele rapide, stage 2: modele precis)
- Branchement de `RerankingConfigV2` au runtime
- Parametres de reranking (batch_size, threshold, top_n) non exposes dans l'UI

---

## Phase 2 : Reranker Local (Cross-Encoder)

### 2.1 Creer `ragkit/retrieval/cross_encoder_reranker.py`

```python
class CrossEncoderReranker(BaseReranker):
    """Reranker utilisant un cross-encoder local."""

    MODELS = {
        "cross-encoder/ms-marco-MiniLM-L-6-v2": {"size_mb": 80, "speed": "fast"},
        "cross-encoder/ms-marco-TinyBERT-L-2-v2": {"size_mb": 50, "speed": "very_fast"},
        "BAAI/bge-reranker-v2-m3": {"size_mb": 500, "speed": "medium"},
    }

    def __init__(self, config: RerankingConfigV2):
        self.model_name = config.reranker_model
        self.batch_size = config.rerank_batch_size
        self.use_gpu = config.use_gpu
        self._model = None

    def _load_model(self):
        """Charge le modele cross-encoder (lazy loading)."""
        from sentence_transformers import CrossEncoder
        device = "cuda" if self.use_gpu else "cpu"
        self._model = CrossEncoder(self.model_name, device=device)

    async def rerank(self, query, results, top_n, relevance_threshold=0.0):
        if not results:
            return []
        if self._model is None:
            self._load_model()

        pairs = [(query, r.chunk.content) for r in results]

        # Batch scoring
        scores = await asyncio.to_thread(
            self._model.predict, pairs, batch_size=self.batch_size
        )

        scored = [(results[i], float(scores[i])) for i in range(len(results))]
        scored.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for result, score in scored[:top_n]:
            if score >= relevance_threshold:
                reranked.append(RetrievalResult(
                    chunk=result.chunk, score=score, retrieval_type="rerank"
                ))
        return reranked
```

### 2.2 Mettre a jour `create_reranker()`

```python
def create_reranker(config) -> BaseReranker:
    if not config.enabled or config.provider == "none":
        return NoOpReranker()
    if config.provider == "cohere":
        return CohereReranker(config)
    if config.provider == "cross_encoder":
        return CrossEncoderReranker(config)
    raise ValueError(f"Unknown rerank provider: {config.provider}")
```

---

## Phase 3 : Reranking Multi-Etapes

### 3.1 Creer `ragkit/retrieval/multi_stage_reranker.py`

```python
class MultiStageReranker(BaseReranker):
    """Pipeline de reranking en plusieurs etapes."""

    def __init__(self, config: RerankingConfigV2):
        self.stage_1 = CrossEncoderReranker(config, model=config.stage_1_model)
        self.stage_2 = CrossEncoderReranker(config, model=config.stage_2_model)
        self.stage_1_keep_top = config.stage_1_keep_top

    async def rerank(self, query, results, top_n, relevance_threshold=0.0):
        # Stage 1 : Modele rapide, filtre large
        stage_1_results = await self.stage_1.rerank(
            query, results, self.stage_1_keep_top, relevance_threshold=0.0
        )
        # Stage 2 : Modele precis, filtre final
        return await self.stage_2.rerank(
            query, stage_1_results, top_n, relevance_threshold
        )
```

---

## Phase 4 : UI - Exposition des Parametres

### Settings.tsx - Enrichir la section Reranking

Ajouter dans l'onglet "advanced" :
- **Provider** : Select (none / cohere / cross_encoder)
- **Model** : Select dynamique selon provider
  - cohere: rerank-english-v3, rerank-multilingual-v3
  - cross_encoder: ms-marco-MiniLM-L-6-v2, ms-marco-TinyBERT, bge-reranker-v2-m3
- **Top N** : Input numerique (defaut: 5)
- **Candidates** : Input numerique (defaut: 40)
- **Relevance Threshold** : Input numerique (defaut: 0.0)
- **Multi-stage** : Checkbox (visible si cross_encoder)
- **Use GPU** : Checkbox (visible si cross_encoder)

---

## Phase 5 : Tests & Validation

### Tests
```
tests/unit/test_rerank.py (enrichir)
  - test_cross_encoder_reranker
  - test_multi_stage_reranker
  - test_create_reranker_cross_encoder
  - test_rerank_empty_results
  - test_rerank_threshold_filtering
  - test_rerank_batch_size
```

### Validation
1. Builder dans `.build/`
2. Selectionner cross_encoder comme provider
3. Verifier le telechargement du modele
4. Comparer les resultats avec et sans reranking
5. Tester le multi-stage

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/retrieval/cross_encoder_reranker.py` |
| CREER | `ragkit/retrieval/multi_stage_reranker.py` |
| MODIFIER | `ragkit/retrieval/rerank.py` (factory) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_rerank.py` |

---

## Criteres de Validation

- [ ] Cross-encoder local fonctionnel
- [ ] Multi-stage reranking fonctionnel
- [ ] Provider cross_encoder dans la factory
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
