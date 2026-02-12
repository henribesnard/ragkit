# Etape 7 : RECHERCHE HYBRIDE (Fusion)

## Objectif
Ameliorer la fusion des resultats semantiques et lexicaux, ajouter les methodes de normalisation, dynamic_alpha, et exposer les parametres dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| ScoreFusion | `ragkit/retrieval/fusion.py` | weighted_sum, reciprocal_rank_fusion, apply() |
| FusionConfig | `ragkit/config/schema.py` | method (weighted_sum/rrf), normalize_scores, rrf_k |
| RetrievalConfigV2 | `ragkit/config/schema_v2.py` | alpha, fusion_method (rrf/linear/weighted_sum/relative_score), normalization_method, dynamic_alpha - NON branche |
| UI | `Settings.tsx` | semantic_weight, lexical_weight |

### Ce qui manque
- `normalization_method` (min-max, z-score, softmax) non branche
- `dynamic_alpha` (ajustement automatique selon le type de requete)
- Methode de fusion `relative_score` non implementee
- Methode de fusion `linear` non implementee
- Exposition des parametres de fusion dans l'UI

---

## Phase 2 : Normalisation des Scores

### 2.1 Modifier `ragkit/retrieval/fusion.py`

Ajouter les methodes de normalisation :

```python
class ScoreNormalizer:
    @staticmethod
    def normalize(scores: list[float], method: str) -> list[float]:
        if method == "min-max":
            return ScoreNormalizer._min_max(scores)
        elif method == "z-score":
            return ScoreNormalizer._z_score(scores)
        elif method == "softmax":
            return ScoreNormalizer._softmax(scores)
        return scores

    @staticmethod
    def _min_max(scores: list[float]) -> list[float]:
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return [1.0] * len(scores)
        return [(s - min_s) / (max_s - min_s) for s in scores]

    @staticmethod
    def _z_score(scores: list[float]) -> list[float]:
        mean = sum(scores) / len(scores)
        std = (sum((s - mean) ** 2 for s in scores) / len(scores)) ** 0.5
        if std == 0:
            return [0.0] * len(scores)
        return [(s - mean) / std for s in scores]

    @staticmethod
    def _softmax(scores: list[float]) -> list[float]:
        import math
        max_s = max(scores)
        exps = [math.exp(s - max_s) for s in scores]
        sum_exps = sum(exps)
        return [e / sum_exps for e in exps]
```

### 2.2 Integrer dans ScoreFusion.weighted_sum

Remplacer la normalisation actuelle (division par max) par la methode configurable.

---

## Phase 3 : Dynamic Alpha

### 3.1 Creer `ragkit/retrieval/alpha_estimator.py`

```python
class DynamicAlphaEstimator:
    """Estime le poids optimal entre semantique et lexical selon la requete."""

    def estimate(self, query: str) -> float:
        """Retourne alpha (poids semantique) entre 0 et 1."""
        # Heuristiques :
        # - Requetes courtes (1-2 mots) -> favoriser lexical (alpha bas)
        # - Requetes longues / questions -> favoriser semantique (alpha haut)
        # - Requetes avec termes techniques exacts -> favoriser lexical
        # - Requetes conceptuelles -> favoriser semantique

        words = query.split()
        if len(words) <= 2:
            return 0.3  # Favorise lexical
        elif query.endswith("?") or any(w in query.lower() for w in ["comment", "pourquoi", "how", "why"]):
            return 0.7  # Favorise semantique
        else:
            return 0.5  # Equilibre
```

### 3.2 Integrer dans le pipeline de retrieval hybride

Si `dynamic_alpha` est active, utiliser `DynamicAlphaEstimator` pour ajuster les poids au lieu d'utiliser les poids fixes.

---

## Phase 4 : Methodes de Fusion Supplementaires

### 4.1 Linear combination

```python
@staticmethod
def linear_combination(results_by_type, alpha, normalize_method="min-max"):
    """Combinaison lineaire simple : score = alpha * semantic + (1-alpha) * lexical."""
```

### 4.2 Relative Score Fusion

```python
@staticmethod
def relative_score_fusion(results_by_type, weights):
    """Fusion basee sur le rang relatif des resultats dans chaque liste."""
```

---

## Phase 5 : UI - Exposition des Parametres

### Settings.tsx - Enrichir la section Retrieval

Ajouter (visible si architecture = hybrid ou hybrid_rerank) :
- **Fusion Method** : Select (weighted_sum / rrf / linear / relative_score)
- **Normalization Method** : Select (min-max / z-score / softmax)
- **RRF k** : Input numerique (defaut: 60, visible si method = rrf)
- **Dynamic Alpha** : Checkbox (defaut: false)

---

## Phase 6 : Tests & Validation

### Tests
```
tests/unit/test_retrieval.py (enrichir)
  - test_min_max_normalization
  - test_z_score_normalization
  - test_softmax_normalization
  - test_dynamic_alpha_short_query
  - test_dynamic_alpha_question
  - test_linear_combination
  - test_relative_score_fusion
```

### Validation
1. Builder dans `.build/`
2. Tester avec requetes courtes vs longues et verifier l'alpha dynamique
3. Comparer les methodes de normalisation
4. Verifier que les parametres de fusion sont dans l'UI

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| MODIFIER | `ragkit/retrieval/fusion.py` |
| CREER | `ragkit/retrieval/alpha_estimator.py` |
| MODIFIER | Pipeline retrieval hybride |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_retrieval.py` |

---

## Criteres de Validation

- [ ] Normalisation configurable (min-max, z-score, softmax)
- [ ] Dynamic alpha fonctionnel
- [ ] Methodes de fusion supplementaires (linear, relative_score)
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
