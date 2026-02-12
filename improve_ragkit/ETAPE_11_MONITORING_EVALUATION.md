# Etape 11 : MONITORING & EVALUATION

## Objectif
Ajouter les metriques de retrieval (precision@k, recall@k, MRR), le feedback utilisateur, et le suivi de performance.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| MetricsConfig | `ragkit/config/schema.py` | enabled, track: list[str] |
| MonitoringConfigV2 | `ragkit/config/schema_v2.py` | Complet (precision@k, recall@k, MRR, nDCG, faithfulness, latency, cost) - NON branche |
| Metrics models | `ragkit/metrics/models.py` | Module present |
| ObservabilityConfig | `ragkit/config/schema.py` | logging, metrics |
| Logs page | `desktop/src/pages/Logs.tsx` | Page de logs existante |
| UI | `Settings.tsx` | Aucun parametre monitoring |

### Ce qui manque
- Metriques de retrieval (precision@k, recall@k, MRR, nDCG)
- Feedback utilisateur (thumbs up/down)
- Metriques de latence (par composant)
- Metriques de generation (faithfulness, relevancy)
- Dashboard de metriques
- Branchement de `MonitoringConfigV2`

---

## Phase 2 : Metriques de Retrieval

### 2.1 Creer `ragkit/metrics/retrieval_metrics.py`

```python
class RetrievalMetrics:
    """Calcule les metriques de qualite du retrieval."""

    @staticmethod
    def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
        """Precision@K : proportion de documents pertinents dans les K premiers."""
        top_k = retrieved[:k]
        relevant_in_top_k = sum(1 for doc in top_k if doc in relevant)
        return relevant_in_top_k / k if k > 0 else 0.0

    @staticmethod
    def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
        """Recall@K : proportion de documents pertinents retrouves dans les K premiers."""
        top_k = retrieved[:k]
        relevant_in_top_k = sum(1 for doc in top_k if doc in relevant)
        return relevant_in_top_k / len(relevant) if relevant else 0.0

    @staticmethod
    def mrr(retrieved: list[str], relevant: set[str]) -> float:
        """Mean Reciprocal Rank : inverse du rang du premier resultat pertinent."""
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                return 1.0 / (i + 1)
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved: list[str], relevant: dict[str, float], k: int) -> float:
        """Normalized Discounted Cumulative Gain."""
        import math
        dcg = sum(
            relevant.get(doc, 0.0) / math.log2(i + 2)
            for i, doc in enumerate(retrieved[:k])
        )
        ideal = sorted(relevant.values(), reverse=True)[:k]
        idcg = sum(score / math.log2(i + 2) for i, score in enumerate(ideal))
        return dcg / idcg if idcg > 0 else 0.0
```

---

## Phase 3 : Suivi de Latence

### 3.1 Creer `ragkit/metrics/latency_tracker.py`

```python
class LatencyTracker:
    """Mesure la latence de chaque composant du pipeline RAG."""

    def __init__(self):
        self._timings: dict[str, list[float]] = defaultdict(list)

    @contextmanager
    def track(self, component: str):
        start = time.perf_counter()
        yield
        elapsed = (time.perf_counter() - start) * 1000  # ms
        self._timings[component].append(elapsed)

    def get_stats(self, component: str) -> dict:
        times = self._timings.get(component, [])
        if not times:
            return {}
        return {
            "count": len(times),
            "mean_ms": sum(times) / len(times),
            "p50_ms": sorted(times)[len(times) // 2],
            "p95_ms": sorted(times)[int(len(times) * 0.95)],
            "p99_ms": sorted(times)[int(len(times) * 0.99)],
        }

    def get_all_stats(self) -> dict:
        return {comp: self.get_stats(comp) for comp in self._timings}
```

### 3.2 Integrer dans le pipeline RAG

```python
async def query(self, question: str):
    with self.latency.track("embedding"):
        query_emb = await self.embedder.embed_query(question)
    with self.latency.track("semantic_search"):
        semantic_results = await self.semantic_retriever.retrieve(question)
    with self.latency.track("lexical_search"):
        lexical_results = self.lexical_retriever.retrieve(question)
    with self.latency.track("fusion"):
        fused = ScoreFusion.apply(...)
    with self.latency.track("reranking"):
        reranked = await self.reranker.rerank(...)
    with self.latency.track("generation"):
        response = await self.generator.generate(...)
```

---

## Phase 4 : Feedback Utilisateur

### 4.1 Backend - API de feedback

Ajouter une route API pour recevoir le feedback :
```python
@router.post("/feedback")
async def submit_feedback(query_id: str, rating: int, comment: str | None = None):
    """Enregistre le feedback utilisateur (1 = positif, -1 = negatif)."""
```

### 4.2 Frontend - Boutons thumbs up/down

Modifier `desktop/src/pages/Chat.tsx` :
- Ajouter des boutons thumbs up / thumbs down apres chaque reponse
- Envoyer le feedback au backend via IPC

### 4.3 Stockage du feedback

Creer `ragkit/metrics/feedback_store.py` :
```python
class FeedbackStore:
    """Stocke et analyse le feedback utilisateur."""

    def save(self, query_id: str, rating: int, query: str, response: str):
        """Sauvegarde le feedback."""

    def get_stats(self) -> dict:
        """Retourne les statistiques de satisfaction."""
        return {
            "total_feedback": ...,
            "positive_rate": ...,
            "negative_rate": ...,
        }
```

---

## Phase 5 : UI - Dashboard & Parametres

### 5.1 Nouvelle page ou section "Monitoring"

- Afficher les statistiques de latence par composant
- Afficher le hit rate du cache
- Afficher le taux de satisfaction (feedback)
- Graphiques de tendance (optionnel)

### 5.2 Settings - Parametres monitoring

Dans l'onglet "advanced" :
- **Track retrieval metrics** : Checkbox
- **Track latency** : Checkbox
- **Log all queries** : Checkbox
- **Feedback enabled** : Checkbox

---

## Phase 6 : Tests & Validation

### Tests
```
tests/unit/test_metrics.py (enrichir)
  - test_precision_at_k
  - test_recall_at_k
  - test_mrr
  - test_ndcg_at_k
  - test_latency_tracker
  - test_feedback_store
```

### Validation
1. Builder dans `.build/`
2. Poser plusieurs questions et verifier les latences dans les logs
3. Utiliser les boutons de feedback
4. Verifier le dashboard de metriques

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/metrics/retrieval_metrics.py` |
| CREER | `ragkit/metrics/latency_tracker.py` |
| CREER | `ragkit/metrics/feedback_store.py` |
| MODIFIER | Pipeline RAG (integration latency tracker) |
| MODIFIER | `ragkit/api/routes/` (route feedback) |
| MODIFIER | `desktop/src/pages/Chat.tsx` (boutons feedback) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| ENRICHIR | `tests/unit/test_metrics.py` |

---

## Criteres de Validation

- [ ] Metriques precision@k, recall@k, MRR calculees
- [ ] Latency tracking par composant
- [ ] Feedback utilisateur (thumbs up/down) fonctionnel
- [ ] Stats de monitoring accessibles
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
