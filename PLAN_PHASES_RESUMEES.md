# Plan RAGKIT v2.0 - Résumé des Phases Restantes

Ce document complète [PLAN_COMPLET_RAGKIT_V2.md](PLAN_COMPLET_RAGKIT_V2.md) en fournissant des résumés structurés des phases 5-12.

Statut actuel: Phase 1 TERMINEE, Phase 2 TERMINEE (2026-02-10).

---

## Phase 5: Retrieval Multi-stratégies

**Objectif**: Implémenter recherche sémantique, lexicale (BM25), et hybride avec fusion

### Paramètres clés (32 paramètres)

#### 5.1 Recherche Sémantique (Dense)
```python
- query_preprocessing: bool
- query_expansion: Literal["none", "synonyms", "llm_rewrite"]
- multi_query_strategy: Literal["single", "multi_perspective", "hyde"]
- top_k: int = 10
- score_threshold: float = 0.0
- mmr_enabled: bool = False
- mmr_lambda: float = 0.5
- diversity_threshold: float = 0.8
- filter_conditions: dict
- filter_mode: Literal["must", "should", "must_not"]
```

#### 5.2 Recherche Lexicale (BM25)
```python
- tokenizer_type: Literal["standard", "whitespace", "ngram"]
- lowercase_tokens: bool = True
- remove_stopwords: bool = True
- stopwords_language: str = "english"
- custom_stopwords: list[str]
- stemming_enabled: bool = False
- lemmatization_enabled: bool = False
- bm25_k1: float = 1.2
- bm25_b: float = 0.75
- bm25_delta: float = 0.5
- ngram_range: tuple[int, int] = (1, 2)
- max_features: int | None = None
```

#### 5.3 Recherche Hybride
```python
- alpha: float = 0.5  # PARAMÈTRE CRITIQUE
- fusion_method: Literal["rrf", "linear", "weighted_sum", "relative_score"]
- rrf_k: int = 60
- normalize_scores: bool = True
- normalization_method: Literal["min-max", "z-score", "softmax"]
- dynamic_alpha: bool = False
- query_classifier_enabled: bool = False
```

### Fichiers à créer/modifier

1. **Backend**:
   - `ragkit/retrieval/semantic_retriever.py` - Recherche dense avancée
   - `ragkit/retrieval/lexical_retriever.py` - BM25 avec tous paramètres
   - `ragkit/retrieval/hybrid_retriever.py` - Fusion intelligente
   - `ragkit/retrieval/query_expander.py` - Expansion de requêtes
   - `ragkit/retrieval/mmr.py` - Maximal Marginal Relevance

2. **Configuration**:
   - Ajouter `RetrievalConfigV2` dans `schema_v2.py`
   - Profils de recherche selon type de KB

3. **Tests**:
   - `tests/test_semantic_retrieval.py` - Test top_k, MMR, filtres
   - `tests/test_bm25.py` - Test tokenization, stemming, paramètres BM25
   - `tests/test_hybrid_fusion.py` - Test RRF, alpha, normalization

### Tests critiques

```python
def test_alpha_technical_docs():
    """Alpha bas favorise lexical pour docs techniques."""
    config = RetrievalConfigV2(alpha=0.3)
    # Requête avec termes techniques exacts
    results = retriever.search("API endpoint POST /users")
    # Doit retrouver docs avec termes exacts

def test_alpha_conceptual():
    """Alpha élevé favorise sémantique pour concepts."""
    config = RetrievalConfigV2(alpha=0.8)
    # Requête conceptuelle
    results = retriever.search("How to secure my application?")
    # Doit retrouver docs parlant de sécurité (synonymes, concepts)

def test_rrf_fusion():
    """RRF combine correctement les rangs."""
    # Mock des résultats sémantiques et lexicaux
    # Vérifier fusion RRF vs linear
```

---

## Phase 6: Reranking & Optimisation

**Objectif**: Ajouter reranking cross-encoder et optimisations multi-étapes

### Paramètres clés (15 paramètres)

```python
class RerankingConfigV2(BaseModel):
    # Modèle
    reranker_model: Literal[
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "BAAI/bge-reranker-v2-m3",
        "cohere-rerank-v3",
        "llm-based",
        "colbert",
    ]
    reranker_enabled: bool = False

    # Paramètres
    rerank_top_n: int = 100  # Candidats à reranker
    rerank_batch_size: int = 16
    rerank_threshold: float = 0.0
    final_top_k: int = 5  # Résultats finaux
    return_scores: bool = True

    # Multi-étapes
    multi_stage_reranking: bool = False
    stage_1_model: str = "fast-reranker"  # Rapide, filtre
    stage_2_model: str = "precise-reranker"  # Précis, final
    stage_1_keep_top: int = 50

    # Performance
    use_gpu: bool = True
    half_precision: bool = False
```

### Implémentations clés

#### 6.1 Cross-Encoder Reranker
- Load model avec cache
- Batch processing optimisé
- Gestion mémoire GPU

#### 6.2 Multi-Stage Reranking
1. **Stage 1**: Modèle léger filtre 100 → 50 candidats
2. **Stage 2**: Modèle précis sélectionne top 5

#### 6.3 ColBERT Reranking
- Interaction fine token-level
- Plus coûteux mais très précis

### Tests

```python
def test_reranking_improves_precision():
    """Le reranking améliore la précision."""
    # Sans reranking
    results_no_rerank = retriever.search(query, rerank=False)

    # Avec reranking
    results_rerank = retriever.search(query, rerank=True)

    # Évaluer avec ground truth
    assert precision(results_rerank) > precision(results_no_rerank)

def test_multi_stage_faster_than_single():
    """Multi-stage plus rapide que stage précis direct."""
    # Mesurer temps
```

---

## Phase 7: LLM & Génération

**Objectif**: Configuration complète de la génération avec prompts, guardrails, citations

### Paramètres clés (30 paramètres)

```python
class LLMGenerationConfigV2(BaseModel):
    # Modèle
    model: str = "gpt-4o-mini"
    provider: str = "openai"

    # Génération
    temperature: float = 0.1  # RAG: bas pour éviter hallucinations
    max_tokens: int = 1000
    top_p: float = 0.9
    top_k: int | None = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Prompt Engineering
    system_prompt: str
    few_shot_examples: list[dict] = []
    chain_of_thought: bool = False
    output_format: Literal["text", "json", "markdown"] = "text"
    json_schema: dict | None = None

    # Context Management
    context_window_strategy: Literal[
        "truncate_middle",
        "summarize_overflow",
        "sliding_window",
    ] = "truncate_middle"
    max_context_tokens: int = 4000
    context_compression: bool = False
    compression_ratio: float = 0.5

    # Citations
    cite_sources: bool = True
    citation_format: Literal["numbered", "footnote", "inline"] = "numbered"
    include_metadata_in_citation: bool = True  # Page, section, date
    citation_template: str = "[Source: {source_name}, p.{page}]"

    # Guardrails
    enable_fallback: bool = True
    fallback_message: str = "Je n'ai pas trouvé d'informations pertinentes."
    confidence_threshold: float = 0.5
    require_citation_for_facts: bool = True
    content_filters: list[str] = ["toxicity", "pii"]
    max_retries: int = 3
```

### Implémentations clés

#### 7.1 Prompt Builder
```python
class PromptBuilder:
    def build_rag_prompt(
        self,
        query: str,
        context_chunks: list[Chunk],
        config: LLMGenerationConfigV2,
    ) -> str:
        """Construit le prompt RAG optimal."""

        # System prompt
        prompt = config.system_prompt + "\n\n"

        # Few-shot examples
        if config.few_shot_examples:
            prompt += "Examples:\n"
            for ex in config.few_shot_examples:
                prompt += f"Q: {ex['question']}\nA: {ex['answer']}\n\n"

        # Context avec citations
        prompt += "Context:\n"
        for i, chunk in enumerate(context_chunks, 1):
            source_info = self._format_source(chunk.metadata, config)
            prompt += f"[{i}] {source_info}\n{chunk.content}\n\n"

        # Question
        if config.chain_of_thought:
            prompt += f"Question: {query}\n"
            prompt += "Let's think step by step:\n"
        else:
            prompt += f"Question: {query}\n"

        # Instructions de citation
        if config.cite_sources:
            prompt += "\nImportant: Cite your sources using [1], [2], etc.\n"

        return prompt
```

#### 7.2 Response Validator
```python
class ResponseValidator:
    def validate(
        self,
        response: str,
        context: list[Chunk],
        config: LLMGenerationConfigV2,
    ) -> ValidationResult:
        """Valide la réponse du LLM."""

        issues = []

        # Vérifier présence citations
        if config.require_citation_for_facts:
            if not self._has_citations(response):
                issues.append("No citations found")

        # Vérifier hallucinations (réponse vs contexte)
        if config.confidence_threshold > 0:
            confidence = self._check_faithfulness(response, context)
            if confidence < config.confidence_threshold:
                issues.append(f"Low confidence: {confidence:.2f}")

        # Content filters
        for filter_type in config.content_filters:
            if self._check_filter(response, filter_type):
                issues.append(f"Content filter triggered: {filter_type}")

        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            confidence=confidence,
        )
```

### Tests

```python
def test_cites_sources():
    """Vérifie que les sources sont citées."""
    response = generator.generate(query, context)
    assert "[1]" in response or "Source:" in response

def test_no_hallucination():
    """Vérifie absence d'hallucinations."""
    # Contexte très spécifique
    context = [Chunk("Python was created in 1991 by Guido van Rossum")]

    response = generator.generate(
        "When was Python created?",
        context,
    )

    assert "1991" in response
    assert "Guido van Rossum" in response
    # Ne doit PAS inventer d'autres infos
    assert "JavaScript" not in response
```

---

## Phase 8: Cache & Performance

**Objectif**: Optimiser latence et coûts via caching multi-niveaux

### Paramètres clés (20 paramètres)

```python
class CacheConfigV2(BaseModel):
    # Query Cache
    query_cache_enabled: bool = True
    query_cache_ttl: int = 3600  # secondes
    query_cache_size_mb: int = 512
    cache_key_strategy: Literal["exact", "fuzzy", "semantic"] = "semantic"
    semantic_cache_threshold: float = 0.95

    # Embedding Cache
    embedding_cache_enabled: bool = True
    embedding_cache_size_mb: int = 1024
    embedding_cache_ttl: int = 86400  # 24h

    # Result Cache
    result_cache_enabled: bool = True
    result_cache_ttl: int = 1800  # 30min

    # Batching & Async
    async_processing: bool = True
    batch_size: int = 32
    concurrent_requests: int = 10
    queue_max_size: int = 1000

    # Warmup
    warmup_enabled: bool = True
    warmup_queries: list[str] = []
    preload_index: bool = False

    # Compression
    compress_cache: bool = True
    compression_algorithm: Literal["gzip", "lz4", "zstd"] = "lz4"
```

### Implémentations

#### 8.1 Semantic Cache
```python
class SemanticCache:
    """Cache basé sur similarité sémantique des requêtes."""

    def get(self, query: str, threshold: float = 0.95) -> CacheEntry | None:
        """Récupère depuis le cache si requête similaire existe."""

        query_embedding = self.embed(query)

        # Chercher dans le cache
        for cached_query, cached_result in self.cache.items():
            similarity = cosine_similarity(
                query_embedding,
                cached_result.query_embedding,
            )

            if similarity >= threshold:
                return cached_result

        return None
```

#### 8.2 Batch Processor
```python
class BatchProcessor:
    """Traite les requêtes par batch pour optimiser."""

    async def process_batch(self, queries: list[str]) -> list[Result]:
        """Traite un batch de requêtes en parallèle."""

        # Embedder tout le batch en une fois
        embeddings = await self.embedder.embed_batch(queries)

        # Rechercher en parallèle
        search_tasks = [
            self.vector_db.search(emb, top_k=10)
            for emb in embeddings
        ]
        search_results = await asyncio.gather(*search_tasks)

        # Générer réponses
        return await self.generate_batch(queries, search_results)
```

### Tests

```python
@pytest.mark.benchmark
def test_cache_reduces_latency(benchmark):
    """Le cache réduit significativement la latence."""

    # Premier appel (sans cache)
    first_latency = benchmark(lambda: rag.query("test"))

    # Deuxième appel (avec cache)
    second_latency = benchmark(lambda: rag.query("test"))

    # Le cache doit réduire latence d'au moins 80%
    assert second_latency < first_latency * 0.2

def test_semantic_cache_hits_similar():
    """Cache sémantique matche les requêtes similaires."""

    rag.query("How to install Python?")

    # Requête similaire
    result = rag.query("What is the Python installation process?")

    # Doit venir du cache (vérifier via logs/metrics)
    assert result.metadata["from_cache"] is True
```

---

## Phase 9: Monitoring & Evaluation

**Objectif**: Métriques complètes et évaluation automatique

### Métriques à implémenter (25 métriques)

#### 9.1 Métriques Retrieval
```python
- precision_at_k
- recall_at_k
- f1_at_k
- mrr (Mean Reciprocal Rank)
- ndcg_at_k (Normalized Discounted Cumulative Gain)
- map (Mean Average Precision)
- hit_rate_at_k
```

#### 9.2 Métriques Génération
```python
- answer_relevance  # Pertinence de la réponse
- faithfulness  # Fidélité aux sources (anti-hallucination)
- context_precision  # Qualité du contexte récupéré
- context_recall  # Complétude du contexte
- answer_correctness  # Exactitude factuelle
- answer_similarity  # Similarité avec ground truth
```

#### 9.3 Métriques Performance
```python
- latency_p50, latency_p95, latency_p99
- throughput_qps  # Queries per second
- cost_per_query  # Tokens utilisés
- cache_hit_rate
- error_rate
```

### Implémentations

```python
# ragkit/evaluation/evaluator.py

class RAGEvaluator:
    """Évalue la qualité du système RAG."""

    def evaluate_retrieval(
        self,
        queries: list[str],
        ground_truth: list[list[str]],  # IDs docs pertinents
        retrieved: list[list[str]],  # IDs docs récupérés
    ) -> dict:
        """Évalue la qualité du retrieval."""

        metrics = {}

        for k in [1, 3, 5, 10]:
            metrics[f"precision@{k}"] = self.precision_at_k(
                ground_truth, retrieved, k
            )
            metrics[f"recall@{k}"] = self.recall_at_k(
                ground_truth, retrieved, k
            )
            metrics[f"ndcg@{k}"] = self.ndcg_at_k(
                ground_truth, retrieved, k
            )

        metrics["mrr"] = self.mean_reciprocal_rank(ground_truth, retrieved)
        metrics["map"] = self.mean_average_precision(ground_truth, retrieved)

        return metrics

    def evaluate_generation(
        self,
        questions: list[str],
        answers: list[str],
        contexts: list[list[str]],
        ground_truth_answers: list[str] | None = None,
    ) -> dict:
        """Évalue la qualité de la génération."""

        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )

        # Utiliser RAGAS pour l'évaluation
        results = evaluate(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truth_answers,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
        )

        return results
```

### Dashboard Monitoring

```python
# ragkit/monitoring/dashboard.py

class MonitoringDashboard:
    """Dashboard en temps réel des métriques."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()

    def get_current_metrics(self) -> dict:
        """Récupère les métriques actuelles."""

        return {
            "latency": {
                "p50": self.metrics_collector.get_percentile(50),
                "p95": self.metrics_collector.get_percentile(95),
                "p99": self.metrics_collector.get_percentile(99),
            },
            "throughput": {
                "qps": self.metrics_collector.get_qps(),
                "total_queries": self.metrics_collector.total_queries,
            },
            "quality": {
                "avg_relevance": self.metrics_collector.avg_answer_relevance,
                "avg_faithfulness": self.metrics_collector.avg_faithfulness,
            },
            "cache": {
                "hit_rate": self.metrics_collector.cache_hit_rate,
                "size_mb": self.metrics_collector.cache_size_mb,
            },
            "costs": {
                "total_tokens": self.metrics_collector.total_tokens,
                "total_cost_usd": self.metrics_collector.total_cost,
            },
        }
```

---

## Phase 10: Security & Compliance

**Objectif**: Sécurité, privacy (RGPD), content moderation

### Paramètres (20 paramètres)

```python
class SecurityConfigV2(BaseModel):
    # Authentification
    access_control_enabled: bool = False
    auth_provider: Literal["local", "oauth", "saml", "ldap"] = "local"
    require_authentication: bool = False

    # Permissions
    document_level_permissions: bool = False
    role_based_access: bool = False
    user_isolation: bool = False

    # Privacy
    pii_detection: bool = False
    pii_redaction: bool = False
    pii_types: list[str] = ["email", "phone", "ssn", "credit_card"]

    # Anonymisation
    anonymize_logs: bool = True
    anonymize_user_queries: bool = False
    data_retention_days: int = 90

    # Content Moderation
    toxicity_filter: bool = True
    toxicity_threshold: float = 0.8
    bias_detection: bool = False
    profanity_filter: bool = False

    # Audit
    audit_logging: bool = True
    audit_log_path: str = "./logs/audit.log"
```

### Implémentations

#### 10.1 PII Detection
```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class PIIDetector:
    def __init__(self, config: SecurityConfigV2):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.config = config

    def detect_and_redact(self, text: str) -> tuple[str, list[dict]]:
        """Détecte et anonymise les PII."""

        if not self.config.pii_detection:
            return text, []

        # Analyser
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=self.config.pii_types,
        )

        # Anonymiser si activé
        if self.config.pii_redaction:
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
            )
            return anonymized.text, results

        return text, results
```

---

## Phase 11: UI/UX Complète

**Objectif**: Interface wizard + dashboard complets selon parcours utilisateur

### Composants UI à créer (20+ composants)

#### 11.1 Wizard (6 étapes)
1. **WelcomeScreen** - Écran bienvenue
2. **ProfileQuestionnaire** - Questions de profilage
3. **ProfileSummary** - Résumé du profil détecté
4. **EnvironmentDetection** - Détection GPU/Ollama
5. **ModelConfiguration** - Config modèles (Ollama/API/Local)
6. **FolderSelection** - Sélection dossier + analyse
7. **IngestionProgress** - Barre progression ingestion
8. **CompletionScreen** - Wizard terminé, lancer dashboard

#### 11.2 Dashboard Principal
- **ServiceStatus** - État services (Embedding, LLM, VectorDB, Reranker)
- **IngestionPanel** - Statut ingestion avec détails
- **ChatInterface** - Chat RAG avec sources cliquables
- **MetricsDashboard** - Latence, coûts, qualité en temps réel

#### 11.3 Paramètres Avancés
- **ChunkingSettings** - Tous paramètres chunking
- **RetrievalSettings** - Alpha, top_k, fusion, etc.
- **LLMSettings** - Temperature, prompts, citations
- **CacheSettings** - Configuration cache
- **SecuritySettings** - PII, moderation

### Gestion de la complexité

**Niveaux de paramètres**:
1. **Simple** (Wizard) - Profils prédéfinis
2. **Intermédiaire** (Settings) - Paramètres principaux (20-30)
3. **Avancé** (Expert mode) - TOUS les paramètres (150+)

**Transitions**:
- Simple → Intermédiaire : Bouton "Paramètres avancés"
- Intermédiaire → Expert : Toggle "Mode expert" dans settings

---

## Phase 12: Tests End-to-End

**Objectif**: Tests complets du système avec datasets de référence

### Datasets de test

1. **SQuAD** - Questions-réponses
2. **MS MARCO** - Information retrieval
3. **Natural Questions** - Google Q&A
4. **HotpotQA** - Multi-hop reasoning

### Scénarios de test

#### 12.1 Test Complet RAG Pipeline
```python
@pytest.mark.e2e
async def test_full_rag_pipeline():
    """Test complet du pipeline RAG."""

    # 1. Ingestion
    docs = load_test_documents()
    await rag.ingest(docs)

    # 2. Query
    query = "What is the capital of France?"
    result = await rag.query(query)

    # 3. Vérifications
    assert "Paris" in result.answer
    assert len(result.sources) > 0
    assert result.latency_ms < 2000  # SLA
    assert result.faithfulness > 0.8  # Qualité
```

#### 12.2 Test Performance
```python
@pytest.mark.benchmark
async def test_latency_sla():
    """Vérifie que le SLA de latence est respecté."""

    queries = load_benchmark_queries(n=100)

    latencies = []
    for query in queries:
        start = time.time()
        await rag.query(query)
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    assert p95 < 2000  # 2s
    assert p99 < 5000  # 5s
```

#### 12.3 Test Qualité
```python
@pytest.mark.quality
async def test_retrieval_quality():
    """Évalue la qualité du retrieval."""

    test_set = load_test_set_with_ground_truth()

    results = []
    for item in test_set:
        retrieved = await rag.retrieve(item.query, top_k=10)
        results.append({
            "query": item.query,
            "retrieved": [doc.id for doc in retrieved],
            "ground_truth": item.relevant_docs,
        })

    metrics = evaluator.evaluate_retrieval(results)

    # Seuils de qualité
    assert metrics["precision@5"] > 0.7
    assert metrics["recall@10"] > 0.8
    assert metrics["ndcg@10"] > 0.75
```

---

## Récapitulatif Final

### Statistiques du plan complet

| Phase | Paramètres | Fichiers | Tests | Complexité |
|-------|------------|----------|-------|------------|
| 1. Wizard | 15 | 8 | 10 | ⭐⭐ |
| 2. Ingestion | 25 | 6 | 15 | ⭐⭐⭐ |
| 3. Chunking | 28 | 7 | 18 | ⭐⭐⭐⭐ |
| 4. Embedding | 22 | 5 | 12 | ⭐⭐⭐ |
| 5. Retrieval | 32 | 9 | 20 | ⭐⭐⭐⭐⭐ |
| 6. Reranking | 15 | 4 | 8 | ⭐⭐⭐ |
| 7. LLM/Gen | 30 | 6 | 15 | ⭐⭐⭐⭐ |
| 8. Cache | 20 | 5 | 10 | ⭐⭐⭐ |
| 9. Monitoring | 25 | 4 | 12 | ⭐⭐ |
| 10. Security | 20 | 6 | 10 | ⭐⭐⭐ |
| 11. UI/UX | — | 25 | 15 | ⭐⭐⭐⭐ |
| 12. E2E Tests | — | 8 | 25 | ⭐⭐⭐ |
| **TOTAL** | **232** | **93** | **170** | — |

### Ordre d'implémentation recommandé

**Sprint 1-2** (Fondations):
- Phase 1: Wizard
- Phase 3: Chunking basique (fixed, sentence)
- Phase 11: UI basique (écrans wizard)

**Sprint 3-4** (Retrieval):
- Phase 4: Embedding basique
- Phase 5: Sémantique + BM25 + Hybride
- Phase 11: Dashboard basique

**Sprint 5-6** (Qualité):
- Phase 2: Parsing avance (OCR, tables) - TERMINEE (2026-02-10)
- Phase 3: Chunking avancé (semantic, parent-child)
- Phase 6: Reranking

**Sprint 7-8** (LLM & Performance):
- Phase 7: Génération complète
- Phase 8: Cache multi-niveaux
- Phase 11: UI complète

**Sprint 9-10** (Production-ready):
- Phase 9: Monitoring
- Phase 10: Security
- Phase 12: Tests E2E

### Critères de validation par phase

Chaque phase ne passe à "Terminé" que si :
1. ✅ Tous les paramètres sont implémentés
2. ✅ Tous les tests unitaires passent
3. ✅ UI correspondante fonctionnelle (si applicable)
4. ✅ Documentation API à jour
5. ✅ Tests E2E passent pour cette fonctionnalité

---

**Ce plan permet de transformer RAGKIT en solution RAG professionnelle avec:**
- ✅ 232 paramètres configurables
- ✅ Wizard intelligent avec profilage automatique
- ✅ Interface simple → intermédiaire → expert
- ✅ Tests exhaustifs (170 tests)
- ✅ Production-ready (monitoring, security, cache)
