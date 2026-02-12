# Etape 3 : EMBEDDING

## Objectif
Ameliorer la configuration des embeddings, ajouter multilingual-e5-large, implementer l'auto-telechargement des modeles, et exposer les parametres avances dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| BaseEmbedder | `ragkit/embedding/base.py` | `embed()`, `embed_query()`, `dimensions` |
| OpenAIEmbedder | `ragkit/embedding/providers/openai.py` | Fonctionnel |
| OllamaEmbedder | `ragkit/embedding/providers/ollama.py` | Fonctionnel |
| CohereEmbedder | `ragkit/embedding/providers/cohere.py` | Fonctionnel |
| LiteLLMEmbedder | `ragkit/embedding/providers/litellm.py` | Fonctionnel |
| ONNX local | Provider existant | Modeles: all-MiniLM-L6-v2, all-mpnet-base-v2, multilingual-e5-small |
| EmbeddingModelConfig | `ragkit/config/schema.py` | provider, model, api_key, params (batch_size, dimensions), cache |
| EmbeddingConfigV2 | `ragkit/config/schema_v2.py` | Complet (normalize, dtype, rate_limit, truncation, pooling, GPU) - NON branche |
| UI | `Settings.tsx` | Provider + model selection |

### Ce qui manque
- multilingual-e5-large dans les modeles ONNX supportes
- Auto-telechargement du modele embedding au premier lancement
- `embedding_batch_size` non expose dans l'UI
- `normalize_embeddings` non expose dans l'UI
- Branchement de `EmbeddingConfigV2` au runtime
- Gestion de la truncation des tokens longs
- Metriques de batch (temps, taille, echecs)

---

## Phase 2 : Ajout de multilingual-e5-large

### 2.1 Provider ONNX

Modifier le provider ONNX local pour supporter `multilingual-e5-large` :
- Ajouter le modele dans la liste des modeles supportes
- Configurer les dimensions (1024 pour e5-large)
- Ajouter les instructions de prefix ("query: " / "passage: " pour e5)

### 2.2 Auto-telechargement

Creer `ragkit/embedding/model_downloader.py` :

```python
class ModelDownloader:
    """Telecharge les modeles ONNX au premier lancement."""

    MODELS = {
        "all-MiniLM-L6-v2": {"url": "...", "size_mb": 80, "dims": 384},
        "all-mpnet-base-v2": {"url": "...", "size_mb": 420, "dims": 768},
        "multilingual-e5-small": {"url": "...", "size_mb": 450, "dims": 384},
        "multilingual-e5-large": {"url": "...", "size_mb": 1100, "dims": 1024},
    }

    def ensure_model(self, model_name: str) -> Path:
        """Verifie que le modele est present, le telecharge sinon."""

    def download_with_progress(self, model_name: str, callback: Callable) -> Path:
        """Telecharge avec callback de progression."""
```

---

## Phase 3 : Branchement Config V2

### 3.1 Normalisation des embeddings

Ajouter dans le pipeline d'embedding :
```python
if config.normalize_embeddings:
    embedding = embedding / np.linalg.norm(embedding)
```

### 3.2 Batching configurable

Exposer `batch_size` dans la configuration et l'utiliser dans tous les providers :
- Limiter le nombre de textes envoyes par batch
- Ajouter un rate limiter si `rate_limit_rpm` est configure

### 3.3 Gestion des tokens longs

Implementer `truncation_strategy` dans le pipeline :
- `start` : Tronquer depuis le debut
- `end` : Tronquer a la fin (defaut)
- `middle` : Garder debut + fin
- `split` : Splitter et moyenner les embeddings

---

## Phase 4 : UI - Exposition des Parametres

### 4.1 Settings.tsx - Enrichir la section Embedding

Dans l'onglet "advanced" (ou dans la carte Embedding existante pour expert) :
- **Batch size** : Input numerique (defaut: 32)
- **Normalize embeddings** : Checkbox (defaut: true)
- **Dimensions** : Affichage informatif des dimensions du modele
- **Modeles ONNX** : Ajouter multilingual-e5-large dans la liste

### 4.2 UI Models

Mettre a jour `EMBEDDING_MODELS` dans Settings.tsx :
```typescript
onnx_local: [
  { value: "all-MiniLM-L6-v2", label: "all-MiniLM-L6-v2 (Fast, 384d)" },
  { value: "all-mpnet-base-v2", label: "all-mpnet-base-v2 (Quality, 768d)" },
  { value: "multilingual-e5-small", label: "multilingual-e5-small (Multilingual, 384d)" },
  { value: "multilingual-e5-large", label: "multilingual-e5-large (Best Quality, 1024d)" },
],
```

---

## Phase 5 : Tests & Validation

### Tests unitaires
```
tests/unit/test_embedding.py (enrichir)
  - test_normalize_embeddings
  - test_batch_size_respected
  - test_model_downloader_cache
  - test_truncation_strategy
  - test_e5_prefix_instructions
```

### Validation
1. Builder dans `.build/`
2. Selectionner multilingual-e5-large dans l'UI
3. Verifier le telechargement automatique
4. Verifier que les embeddings sont normalises
5. Verifier que le batch_size est respecte

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/embedding/model_downloader.py` |
| MODIFIER | Provider ONNX (ajouter multilingual-e5-large) |
| MODIFIER | `ragkit/embedding/base.py` (normalisation) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_embedding.py` |

---

## Criteres de Validation

- [ ] multilingual-e5-large disponible et fonctionnel
- [ ] Auto-telechargement des modeles ONNX
- [ ] normalize_embeddings branche et configurable
- [ ] batch_size branche et configurable
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
