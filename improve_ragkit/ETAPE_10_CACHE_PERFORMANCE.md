# Etape 10 : CACHE & PERFORMANCE

## Objectif
Ajouter un cache de requetes (exact + semantique), un cache d'embeddings, le warmup au demarrage, et optimiser les performances globales.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| EmbeddingCacheConfig | `ragkit/config/schema.py` | enabled, backend (memory/disk) |
| CacheConfigV2 | `ragkit/config/schema_v2.py` | query_cache, embedding_cache, result_cache, async, warmup, compression - NON branche |
| UI | `Settings.tsx` | Aucun parametre cache |

### Ce qui manque
- Cache de requetes (exact match + semantique)
- Cache d'embeddings fonctionnel (existe en config mais non branche)
- Warmup au demarrage (pre-charger l'index, les modeles)
- Batching async pour les requetes
- Compression du cache

---

## Phase 2 : Cache de Requetes

### 2.1 Creer `ragkit/cache/query_cache.py`

```python
class QueryCache:
    """Cache multi-niveau pour les requetes RAG."""

    def __init__(self, config: CacheConfigV2):
        self.config = config
        self._exact_cache: dict[str, CacheEntry] = {}
        self._semantic_cache: list[SemanticCacheEntry] = []
        self._embedder = None  # Pour cache semantique

    def get(self, query: str) -> CachedResult | None:
        """Cherche dans le cache exact puis semantique."""
        # 1. Cache exact
        key = self._hash(query)
        if key in self._exact_cache:
            entry = self._exact_cache[key]
            if not entry.is_expired(self.config.query_cache_ttl):
                return entry.result

        # 2. Cache semantique (si active)
        if self.config.cache_key_strategy == "semantic":
            return self._semantic_lookup(query)

        return None

    def put(self, query: str, result: Any, query_embedding: list[float] | None = None) -> None:
        """Stocke un resultat dans le cache."""
        key = self._hash(query)
        self._exact_cache[key] = CacheEntry(result=result, created_at=time.time())

        if query_embedding and self.config.cache_key_strategy == "semantic":
            self._semantic_cache.append(
                SemanticCacheEntry(query=query, embedding=query_embedding, result=result, created_at=time.time())
            )

    def _semantic_lookup(self, query: str) -> CachedResult | None:
        """Recherche par similarite semantique dans le cache."""
        # Comparer l'embedding de la requete avec les entrees du cache
        # Retourner si similarite > config.semantic_cache_threshold

    def _hash(self, query: str) -> str:
        import hashlib
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def clear(self) -> None:
        self._exact_cache.clear()
        self._semantic_cache.clear()

    def stats(self) -> dict:
        return {
            "exact_entries": len(self._exact_cache),
            "semantic_entries": len(self._semantic_cache),
            "hit_rate": self._hits / max(self._total, 1),
        }
```

---

## Phase 3 : Cache d'Embeddings

### 3.1 Creer `ragkit/cache/embedding_cache.py`

```python
class EmbeddingCache:
    """Cache les embeddings pour eviter les recalculs."""

    def __init__(self, config: CacheConfigV2):
        self.config = config
        self._cache: dict[str, list[float]] = {}
        self._max_size = config.embedding_cache_size_mb * 1024 * 1024  # en bytes

    def get(self, text: str) -> list[float] | None:
        key = self._hash(text)
        return self._cache.get(key)

    def put(self, text: str, embedding: list[float]) -> None:
        key = self._hash(text)
        self._cache[key] = embedding
        self._evict_if_needed()

    def get_batch(self, texts: list[str]) -> tuple[list[list[float] | None], list[int]]:
        """Retourne les embeddings en cache et les indices manquants."""
        results = []
        missing_indices = []
        for i, text in enumerate(texts):
            cached = self.get(text)
            results.append(cached)
            if cached is None:
                missing_indices.append(i)
        return results, missing_indices
```

### 3.2 Integrer dans le pipeline d'embedding

Wrapper les appels embed() pour passer par le cache :
```python
class CachedEmbedder(BaseEmbedder):
    def __init__(self, inner: BaseEmbedder, cache: EmbeddingCache):
        self.inner = inner
        self.cache = cache

    async def embed(self, texts: list[str]) -> list[list[float]]:
        cached, missing = self.cache.get_batch(texts)
        if not missing:
            return cached  # Tout est en cache

        # Calculer les manquants
        missing_texts = [texts[i] for i in missing]
        new_embeddings = await self.inner.embed(missing_texts)

        # Stocker et assembler
        for i, emb in zip(missing, new_embeddings):
            self.cache.put(texts[i], emb)
            cached[i] = emb

        return cached
```

---

## Phase 4 : Warmup au Demarrage

### 4.1 Creer `ragkit/cache/warmup.py`

```python
class WarmupManager:
    """Pre-charge les composants au demarrage."""

    def __init__(self, config: CacheConfigV2):
        self.config = config

    async def warmup(self, components: dict) -> dict:
        """Execute le warmup des composants."""
        results = {}

        # 1. Pre-charger l'index vectoriel
        if self.config.preload_index:
            await components["vector_store"].count()  # Force le chargement
            results["vector_store"] = "loaded"

        # 2. Pre-charger l'index lexical
        if "lexical_retriever" in components:
            results["lexical_index"] = "loaded"

        # 3. Executer les requetes de warmup
        if self.config.warmup_queries:
            for query in self.config.warmup_queries:
                # Executer la requete pour remplir les caches
                pass
            results["warmup_queries"] = len(self.config.warmup_queries)

        return results
```

---

## Phase 5 : UI - Exposition des Parametres

### Settings.tsx - Nouvelle section "Cache & Performance"

Ajouter dans l'onglet "advanced" :
- **Query Cache** : Checkbox enabled (defaut: true)
- **Cache Strategy** : Select (exact / fuzzy / semantic)
- **Cache TTL** : Input numerique (secondes, defaut: 3600)
- **Embedding Cache** : Checkbox enabled (defaut: true)
- **Warmup** : Checkbox enabled (defaut: false)

---

## Phase 6 : Tests & Validation

### Tests
```
tests/unit/test_cache.py
  - test_query_cache_exact_hit
  - test_query_cache_exact_miss
  - test_query_cache_ttl_expiry
  - test_semantic_cache_similar_query
  - test_embedding_cache_batch
  - test_cached_embedder_wrapper
  - test_cache_stats

tests/integration/test_cache_pipeline.py
  - test_query_cache_in_rag_pipeline
  - test_warmup_execution
```

### Validation
1. Builder dans `.build/`
2. Poser la meme question 2 fois -> la 2e doit etre significativement plus rapide
3. Verifier les stats du cache dans les logs
4. Tester le warmup au demarrage

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/cache/__init__.py` |
| CREER | `ragkit/cache/query_cache.py` |
| CREER | `ragkit/cache/embedding_cache.py` |
| CREER | `ragkit/cache/warmup.py` |
| MODIFIER | Pipeline d'embedding (wrapper cache) |
| MODIFIER | Pipeline RAG (integration query cache) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| CREER | `tests/unit/test_cache.py` |

---

## Criteres de Validation

- [ ] Query cache exact fonctionnel
- [ ] Query cache semantique fonctionnel
- [ ] Embedding cache fonctionnel
- [ ] Warmup au demarrage fonctionnel
- [ ] Hit rate mesurable dans les stats
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
