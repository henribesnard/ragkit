# Etape 6 : RECHERCHE LEXICALE

## Objectif
Corriger le bug critique de l'index lexical non alimente, persister l'index BM25, enrichir avec les metadonnees, et exposer les parametres dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| LexicalRetriever | `ragkit/retrieval/lexical.py` | index(), retrieve() avec BM25Okapi/BM25Plus |
| TextPreprocessor | `ragkit/retrieval/lexical.py` | tokenize, lowercase, remove_stopwords, stemming |
| LexicalRetrievalConfig | `ragkit/config/schema.py` | enabled, weight, top_k, algorithm, params (k1, b), preprocessing |
| RetrievalConfigV2 | `ragkit/config/schema_v2.py` | bm25_k1, bm25_b, bm25_delta, ngram_range, etc. - NON branche |
| Stopwords | `ragkit/retrieval/lexical.py` | Francais + Anglais hardcodes |
| Stemming | `ragkit/retrieval/lexical.py` | Simple suffix stripping |
| UI | `Settings.tsx` | lexical_weight seulement |

### BUGS CRITIQUES
1. **L'index lexical n'est JAMAIS alimente dans le pipeline d'ingestion** - `LexicalRetriever.index()` n'est appele nulle part automatiquement lors de l'ingestion
2. **L'index BM25 n'est PAS persiste** - Perdu a chaque redemarrage du backend
3. **Seul le `content` est indexe** - Les metadonnees (title, source) ne sont pas incluses

---

## Phase 2 : Correction du Bug Critique - Alimentation de l'Index

### 2.1 Brancher dans le pipeline d'ingestion

Trouver le point d'ingestion ou les chunks sont envoyes au vector store, et ajouter l'alimentation de l'index lexical :

```python
# Dans le pipeline d'ingestion, apres l'ajout au vector store :
if self.lexical_retriever is not None and config.retrieval.lexical.enabled:
    self.lexical_retriever.index(chunks)
```

### 2.2 Mode incremental

L'index() actuel remplace tous les chunks. Ajouter un mode incremental :

```python
class LexicalRetriever:
    def add_to_index(self, new_chunks: list[Chunk]) -> None:
        """Ajoute des chunks a l'index existant sans tout reconstruire."""
        self.chunks.extend(new_chunks)
        self._rebuild_bm25()

    def _rebuild_bm25(self) -> None:
        """Reconstruit l'index BM25 a partir des chunks courants."""
        tokenized = [self._tokenize_for_index(chunk) for chunk in self.chunks]
        if self.config.algorithm == "bm25+":
            self.bm25 = BM25Plus(tokenized, k1=self.config.params.k1, b=self.config.params.b)
        else:
            self.bm25 = BM25Okapi(tokenized, k1=self.config.params.k1, b=self.config.params.b)
```

---

## Phase 3 : Persistance de l'Index BM25

### 3.1 Creer `ragkit/retrieval/lexical_store.py`

```python
class LexicalStore:
    """Persistance de l'index BM25 sur disque."""

    def __init__(self, path: Path):
        self.path = path

    def save(self, retriever: LexicalRetriever) -> None:
        """Sauvegarde l'index sur disque (pickle ou JSON)."""
        data = {
            "chunks": [chunk.model_dump() for chunk in retriever.chunks],
            "config": retriever.config.model_dump(),
        }
        with open(self.path, "wb") as f:
            pickle.dump(data, f)

    def load(self, config: LexicalRetrievalConfig) -> LexicalRetriever | None:
        """Charge l'index depuis le disque."""
        if not self.path.exists():
            return None
        with open(self.path, "rb") as f:
            data = pickle.load(f)
        retriever = LexicalRetriever(config)
        chunks = [Chunk.model_validate(c) for c in data["chunks"]]
        retriever.index(chunks)
        return retriever
```

### 3.2 Integrer au demarrage

Au demarrage du backend :
1. Tenter de charger l'index depuis le disque
2. Si absent ou invalide, marquer comme "a reconstruire"
3. Lors de la prochaine ingestion, reconstruire et sauvegarder

---

## Phase 4 : Indexation des Metadonnees

### 4.1 Modifier la tokenisation pour inclure les metadonnees

```python
def _tokenize_for_index(self, chunk: Chunk) -> list[str]:
    """Tokenise le contenu + metadonnees pertinentes."""
    parts = [chunk.content]
    if chunk.metadata.get("title"):
        parts.append(chunk.metadata["title"])
    if chunk.metadata.get("source"):
        parts.append(chunk.metadata["source"])
    if chunk.metadata.get("tags"):
        parts.extend(chunk.metadata["tags"])
    combined = " ".join(parts)
    return self.preprocessor.tokenize(combined)
```

---

## Phase 5 : Parametres Avances

### 5.1 bm25_delta (pour BM25+)

Brancher le parametre `delta` de BM25+ qui n'est pas actuellement passe :
```python
self.bm25 = BM25Plus(tokenized, k1=config.params.k1, b=config.params.b, delta=config.params.delta)
```

### 5.2 Stemming ameliore

Remplacer le simple suffix stripping par un vrai stemmer :
```python
def _stem(token: str, language: str = "french") -> str:
    try:
        from nltk.stem.snowball import SnowballStemmer
        stemmer = SnowballStemmer(language)
        return stemmer.stem(token)
    except ImportError:
        return _simple_stem(token)  # Fallback actuel
```

### 5.3 Lemmatisation (optionnelle)

Ajouter le support de la lemmatisation via spaCy si disponible :
```python
def _lemmatize(tokens: list[str], language: str) -> list[str]:
    try:
        import spacy
        nlp = spacy.load(f"{language}_core_web_sm")
        doc = nlp(" ".join(tokens))
        return [token.lemma_ for token in doc]
    except Exception:
        return tokens
```

### 5.4 N-grams

Ajouter le support des n-grams dans la tokenisation :
```python
def _add_ngrams(tokens: list[str], n_range: tuple[int, int] = (1, 2)) -> list[str]:
    result = list(tokens)  # Unigrams
    for n in range(n_range[0], n_range[1] + 1):
        if n > 1:
            result.extend("_".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1))
    return result
```

### 5.5 Custom stopwords

Permettre l'ajout de stopwords personnalises :
```python
stopwords = _get_stopwords(config.preprocessing.stopwords_lang)
if config.preprocessing.custom_stopwords:
    stopwords |= set(config.preprocessing.custom_stopwords)
```

---

## Phase 6 : UI - Exposition des Parametres

### Settings.tsx - Section Recherche Lexicale

Ajouter dans l'onglet "advanced" (visible si architecture inclut lexical) :
- **Algorithm** : Select (bm25 / bm25+)
- **BM25 k1** : Input numerique (defaut: 1.5)
- **BM25 b** : Input numerique (defaut: 0.75)
- **BM25 delta** : Input numerique (defaut: 0.5, visible si bm25+)
- **Stemming** : Checkbox
- **Lemmatization** : Checkbox
- **Stopwords language** : Select (french / english / auto)
- **N-grams** : Checkbox + range

---

## Phase 7 : Tests & Validation

### Tests unitaires
```
tests/unit/test_retrieval.py (enrichir)
  - test_lexical_index_populated_at_ingestion
  - test_lexical_index_persistence
  - test_lexical_index_incremental
  - test_metadata_in_lexical_index
  - test_bm25_delta
  - test_stemming_snowball
  - test_ngrams
  - test_custom_stopwords
```

### Tests d'integration
```
tests/integration/test_lexical_pipeline.py
  - test_ingestion_populates_lexical_index
  - test_lexical_search_after_restart
  - test_lexical_search_includes_metadata
```

### Validation
1. Builder dans `.build/`
2. Ingester des documents
3. Verifier que la recherche lexicale retourne des resultats (BUG CRITIQUE corrige)
4. Redemarrer l'application et verifier que l'index est preserve
5. Tester les parametres BM25 dans l'UI

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| MODIFIER | `ragkit/retrieval/lexical.py` (incremental, metadata, stemming) |
| CREER | `ragkit/retrieval/lexical_store.py` |
| MODIFIER | Pipeline d'ingestion (brancher LexicalRetriever.index) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_retrieval.py` |
| CREER | `tests/integration/test_lexical_pipeline.py` |

---

## Criteres de Validation

- [ ] **BUG CRITIQUE** : L'index lexical est alimente lors de l'ingestion
- [ ] L'index BM25 persiste sur disque et survit aux redemarrages
- [ ] Les metadonnees (title, source, tags) sont incluses dans l'index
- [ ] bm25_delta branche pour BM25+
- [ ] Stemming ameliore (Snowball si dispo)
- [ ] N-grams fonctionnels
- [ ] Custom stopwords fonctionnels
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
