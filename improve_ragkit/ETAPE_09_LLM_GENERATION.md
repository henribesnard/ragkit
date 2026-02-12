# Etape 9 : LLM / GENERATION

## Objectif
Enrichir les parametres de generation LLM, ajouter les penalites, le format de citation configurable, le confidence threshold, et exposer dans l'UI.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| LLMConfig | `ragkit/config/schema.py` | primary/secondary/fast models avec provider/model/api_key/params |
| LLMParams | `ragkit/config/schema.py` | temperature, max_tokens, top_p |
| ResponseBehaviorConfig | `ragkit/config/schema.py` | cite_sources, citation_format, admit_uncertainty, uncertainty_phrase, response_language |
| ResponseGeneratorConfig | `ragkit/config/schema.py` | llm, behavior, system_prompt, no_retrieval_prompt, out_of_scope_prompt |
| LLMGenerationConfigV2 | `ragkit/config/schema_v2.py` | Complet (frequency/presence_penalty, chain_of_thought, context_ordering, confidence_threshold, content_filters) - NON branche |
| LLM module | `ragkit/llm/` | Module present |
| UI | `Settings.tsx` | provider, model, temperature, max_tokens, top_p, system_prompt |

### Ce qui manque
- `frequency_penalty` et `presence_penalty` non exposes dans l'UI
- `citation_format` configurable (inline, footnote, numbered) non branche
- `confidence_threshold` non implemente (repondre "je ne sais pas" si score trop bas)
- Context management (ordering: lost_in_middle, truncation strategy)
- Branchement de `LLMGenerationConfigV2` au runtime

---

## Phase 2 : Frequency & Presence Penalty

### 2.1 Ajouter dans LLMParams

Modifier `ragkit/config/schema.py` :
```python
class LLMParams(BaseModel):
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
```

### 2.2 Passer aux appels LLM

S'assurer que `frequency_penalty` et `presence_penalty` sont passes dans les appels a l'API LLM (OpenAI, Anthropic, etc.).

---

## Phase 3 : Citation Format Configurable

### 3.1 Creer `ragkit/generation/citation.py`

```python
class CitationFormatter:
    """Formate les citations selon le style configure."""

    def __init__(self, format: str = "numbered"):
        self.format = format

    def format_citations(self, sources: list[dict]) -> str:
        if self.format == "numbered":
            return self._numbered(sources)
        elif self.format == "footnote":
            return self._footnote(sources)
        elif self.format == "inline":
            return self._inline(sources)
        return ""

    def _numbered(self, sources):
        """[1] Source Name, p.42"""
        lines = []
        for i, src in enumerate(sources, 1):
            lines.append(f"[{i}] {src.get('name', 'Unknown')}")
        return "\n".join(lines)

    def _footnote(self, sources):
        """Source Name^1"""

    def _inline(self, sources):
        """(Source: Name, p.42)"""

    def get_instruction_for_prompt(self) -> str:
        """Retourne l'instruction de citation a inclure dans le system prompt."""
        if self.format == "numbered":
            return "Cite each fact using numbered references like [1], [2]. List sources at the end."
        elif self.format == "footnote":
            return "Add footnote references using superscript numbers."
        elif self.format == "inline":
            return "Cite sources inline using (Source: name) format."
        return ""
```

---

## Phase 4 : Confidence Threshold

### 4.1 Implementer dans le pipeline de generation

```python
class ResponseGenerator:
    async def generate(self, query, context_results, config):
        # Verifier le score de confiance
        if config.confidence_threshold > 0 and context_results:
            max_score = max(r.score for r in context_results)
            if max_score < config.confidence_threshold:
                return GeneratedResponse(
                    content=config.fallback_message,
                    sources=[],
                    metadata={"confidence": max_score, "below_threshold": True}
                )

        # Generation normale...
```

---

## Phase 5 : Context Management

### 5.1 Context Ordering

Implementer les strategies d'ordonnancement du contexte :

```python
def order_context(results: list[RetrievalResult], strategy: str) -> list[RetrievalResult]:
    if strategy == "relevance":
        return sorted(results, key=lambda r: r.score, reverse=True)
    elif strategy == "chronological":
        return sorted(results, key=lambda r: r.chunk.metadata.get("chunk_index", 0))
    elif strategy == "lost_in_middle":
        # Les documents les plus pertinents en debut et fin
        # Les moins pertinents au milieu (Liu et al., 2023)
        sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
        n = len(sorted_results)
        reordered = []
        for i in range(0, n, 2):
            reordered.append(sorted_results[i])
        for i in range(n - 1 if n % 2 == 0 else n - 2, 0, -2):
            reordered.append(sorted_results[i])
        return reordered
    return results
```

---

## Phase 6 : UI - Exposition des Parametres

### Settings.tsx - Enrichir les sections LLM

**Onglet general** (existant, enrichir) :
- Ajouter `frequency_penalty` : Input numerique (-2 a 2, defaut: 0)
- Ajouter `presence_penalty` : Input numerique (-2 a 2, defaut: 0)

**Onglet advanced** (nouveau ou existant) :
- **Citation Format** : Select (numbered / footnote / inline)
- **Confidence Threshold** : Input numerique (0 a 1, defaut: 0.5)
- **Fallback Message** : Textarea
- **Context Ordering** : Select (relevance / chronological / lost_in_middle)

---

## Phase 7 : Tests & Validation

### Tests
```
tests/unit/test_llm.py (enrichir)
  - test_frequency_penalty_passed
  - test_presence_penalty_passed
  - test_citation_format_numbered
  - test_citation_format_footnote
  - test_citation_format_inline
  - test_confidence_threshold_below
  - test_confidence_threshold_above
  - test_context_ordering_relevance
  - test_context_ordering_lost_in_middle
```

### Validation
1. Builder dans `.build/`
2. Modifier les penalites dans l'UI et verifier l'impact sur les reponses
3. Changer le format de citation et verifier
4. Baisser le confidence threshold et poser une question hors contexte -> "je ne sais pas"
5. Tester lost_in_middle ordering

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| MODIFIER | `ragkit/config/schema.py` (LLMParams) |
| CREER | `ragkit/generation/citation.py` |
| MODIFIER | Pipeline de generation (confidence threshold, context ordering) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| ENRICHIR | `tests/unit/test_llm.py` |

---

## Criteres de Validation

- [ ] frequency_penalty et presence_penalty branches et fonctionnels
- [ ] Citation format configurable (numbered, footnote, inline)
- [ ] Confidence threshold implemente
- [ ] Context ordering implemente (lost_in_middle)
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
