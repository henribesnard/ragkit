# RAGKIT — Contexte du Projet

## 📋 Vue d'Ensemble

### Qu'est-ce que RAGKIT ?

**RAGKIT** est un framework open-source de RAG (Retrieval-Augmented Generation) agentique **entièrement configurable via fichiers YAML**. L'objectif est de permettre à n'importe quel développeur ou équipe technique de déployer un système RAG complet avec chatbot **sans écrire une seule ligne de code applicatif**.

### Positionnement Marché

RAGKIT se positionne dans un espace vacant entre :

| Catégorie | Exemples | Limitation |
|-----------|----------|------------|
| Frameworks code-first | LangChain, LlamaIndex, Haystack | Nécessitent beaucoup de code Python |
| Plateformes no-code | Dify, Flowise | RAG basique, peu de contrôle fin |
| Solutions spécialisées | RAGFlow | Complexes à étendre, focus parsing |

**RAGKIT comble ce gap** : la puissance d'un framework code-first avec la simplicité d'une configuration déclarative.

---

## 🎯 Philosophie de Conception

### Principes Fondamentaux

```
1. Configuration > Code
   → Tout doit être configurable en YAML
   → Le code runtime est générique et piloté par la config

2. Modulaire > Monolithique
   → Chaque composant est indépendant et remplaçable
   → Les providers (LLM, embedding, vector store) sont interchangeables

3. Explicite > Magique
   → Pas de comportement caché ou par défaut non documenté
   → La config reflète exactement ce qui sera exécuté

4. Production-Ready dès le départ
   → Logging, métriques, évaluation intégrés
   → Gestion des erreurs et retry robuste
```

### Ce que RAGKIT N'EST PAS

- ❌ Un framework de développement LLM généraliste (pas un concurrent de LangChain)
- ❌ Une plateforme avec interface graphique de création (pas un concurrent de Dify)
- ❌ Un outil de parsing de documents (pas un concurrent de RAGFlow/Unstructured)
- ❌ Une base de données vectorielle (utilise les solutions existantes)

### Ce que RAGKIT EST

- ✅ Un **runtime RAG configurable** qui orchestre les meilleurs composants existants
- ✅ Un **système déclaratif** où YAML = comportement du système
- ✅ Un **orchestrateur d'agents** simple et prédictible
- ✅ Une **solution clé-en-main** avec chatbot et API intégrés

---

## 🏗️ Architecture Technique

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RAGKIT RUNTIME                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │    CONFIG    │     │   INGESTION  │     │   RETRIEVAL  │                │
│  │    LOADER    │────▶│   PIPELINE   │────▶│    ENGINE    │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                                          │                        │
│         │                                          ▼                        │
│         │                                  ┌──────────────┐                 │
│         │                                  │    AGENTS    │                 │
│         │                                  │    SYSTEM    │                 │
│         │                                  └──────────────┘                 │
│         │                                          │                        │
│         ▼                                          ▼                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     UNIFIED CONFIGURATION                            │   │
│  │                        (ragkit.yaml)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  INTERFACES                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   CHATBOT    │  │   REST API   │  │  WEBSOCKET   │  │   METRICS    │    │
│  │      UI      │  │   ENDPOINTS  │  │    SERVER    │  │  DASHBOARD   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Composants Principaux

#### 1. Config Loader
- Parse et valide les fichiers YAML
- Gère l'héritage et les overrides d'environnement
- Résout les variables d'environnement (`*_env`)

#### 2. Ingestion Pipeline
- Charge les documents depuis les sources configurées
- Applique le parsing (PDF, DOCX, etc.)
- Découpe en chunks selon la stratégie choisie
- Génère les embeddings et stocke dans le vector store

#### 3. Retrieval Engine
- Exécute la recherche sémantique et/ou lexicale
- Applique la fusion des scores
- Gère le reranking si configuré
- Retourne les chunks pertinents avec métadonnées

#### 4. Agents System (V1 Simplifié)
- **Query Analyzer** : Analyse la requête, décide si RAG nécessaire
- **Response Generator** : Génère la réponse finale avec contexte

#### 5. Interfaces
- **Chatbot UI** : Interface web intégrée (Gradio/Streamlit)
- **REST API** : Endpoints pour intégration
- **Streaming** : configurable côté utilisateur (chatbot et API SSE)

---

## 📦 Stack Technique Cible

### Langage et Runtime
- **Python 3.10+** (langage principal)
- **asyncio** (toutes les I/O sont async)
- **Pydantic v2** (validation des configs et modèles)

### Dépendances Principales

| Catégorie | Librairie | Justification |
|-----------|-----------|---------------|
| Config | `pydantic-settings`, `PyYAML` | Validation stricte, parsing YAML |
| LLM | `litellm` | Abstraction multi-provider uniforme |
| Embedding | `litellm` + providers natifs | Flexibilité maximale |
| Vector Store | Clients natifs (qdrant-client, etc.) | Performance optimale |
| Parsing | `unstructured`, `docling` | Meilleurs parsers disponibles |
| Chunking | Custom + `langchain-text-splitters` | Contrôle fin |
| API | `FastAPI` | Async natif, OpenAPI auto |
| Chatbot UI | `Gradio` | Simple, personnalisable |
| Observability | `opentelemetry`, `structlog` | Standard industrie |

### Pourquoi ces choix ?

**LiteLLM** plutôt que clients natifs pour LLM :
- Interface unifiée pour 100+ providers
- Gestion automatique des retry/fallback
- Pas de lock-in provider

**Clients natifs** pour Vector Stores :
- Performance critique pour le retrieval
- Features spécifiques (filtres, quantization)
- LiteLLM ne couvre pas ce besoin

---

## 🔄 Flux de Données V1

### Flux d'Ingestion

```
Documents (PDF, DOCX, MD, ...)
         │
         ▼
┌─────────────────┐
│  Source Loader  │  ← Charge depuis local/S3/web
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Parser      │  ← Extrait le texte (unstructured/docling)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Chunker      │  ← Découpe selon stratégie configurée
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Embedder     │  ← Génère les vecteurs (batch)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vector Store   │  ← Stocke chunks + embeddings + metadata
└─────────────────┘
```

### Flux de Query (V1)

```
User Query
    │
    ▼
┌──────────────────┐
│  Query Analyzer  │  ← Analyse : RAG nécessaire ? Reformulation ?
│     (Agent 1)    │
└────────┬─────────┘
         │
         │ Si RAG nécessaire
         ▼
┌──────────────────┐
│ Retrieval Engine │
│                  │
│  ┌────────────┐  │
│  │  Semantic  │  │  ← Recherche vectorielle
│  │   Search   │  │
│  └─────┬──────┘  │
│        │         │
│  ┌─────▼──────┐  │
│  │  Lexical   │  │  ← BM25 (optionnel)
│  │   Search   │  │
│  └─────┬──────┘  │
│        │         │
│  ┌─────▼──────┐  │
│  │   Fusion   │  │  ← Combine les scores
│  └─────┬──────┘  │
│        │         │
│  ┌─────▼──────┐  │
│  │  Reranker  │  │  ← Rerank (optionnel)
│  └─────┬──────┘  │
└────────┼─────────┘
         │
         ▼
┌──────────────────┐
│    Response      │  ← Génère la réponse avec contexte
│    Generator     │
│    (Agent 2)     │
└────────┬─────────┘
         │
         ▼
    Final Response
    (+ sources)
```

---

## 🎯 Scope V1

### Inclus dans V1

| Composant | Features |
|-----------|----------|
| **Config** | Loader YAML, validation Pydantic, env vars |
| **Ingestion** | Local files (PDF, DOCX, MD, TXT), chunking (fixed, semantic) |
| **Embedding** | OpenAI, Ollama, Cohere |
| **Vector Store** | Qdrant, ChromaDB |
| **Retrieval** | Semantic, Lexical (BM25), Hybrid, Rerank (Cohere) |
| **LLM** | OpenAI, Anthropic, Ollama |
| **Agents** | Query Analyzer, Response Generator (agents par défaut) |
| **Chatbot** | Interface Gradio basique |
| **API** | Endpoints query, health |
| **CLI** | init, ingest, serve, query |

### Exclus de V1 (Roadmap)

- Multi-agent personnalisé / orchestrateur custom
- Sources : S3, Notion, Confluence, GitHub
- GraphRAG
- Évaluation automatique (RAGAS)
- Multi-tenancy
- Authentication
- Interface d'administration

---

## 📁 Structure du Projet

```
ragkit/
├── pyproject.toml              # Dependencies et metadata
├── README.md                   # Documentation utilisateur
├── LICENSE                     # Apache 2.0
│
├── ragkit/                     # Package principal
│   ├── __init__.py
│   ├── __main__.py             # Entry point CLI
│   │
│   ├── config/                 # Configuration
│   │   ├── __init__.py
│   │   ├── loader.py           # Charge et parse YAML
│   │   ├── schema.py           # Modèles Pydantic
│   │   └── validators.py       # Validations custom
│   │
│   ├── ingestion/              # Pipeline d'ingestion
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Orchestrateur ingestion
│   │   ├── sources/            # Loaders par source
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── local.py
│   │   │   └── web.py
│   │   ├── parsers/            # Parsers par format
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── pdf.py
│   │   │   ├── docx.py
│   │   │   └── markdown.py
│   │   └── chunkers/           # Stratégies de chunking
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── fixed.py
│   │       └── semantic.py
│   │
│   ├── embedding/              # Embedding
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── openai.py
│   │       ├── ollama.py
│   │       └── cohere.py
│   │
│   ├── vectorstore/            # Vector stores
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── qdrant.py
│   │       └── chroma.py
│   │
│   ├── retrieval/              # Retrieval engine
│   │   ├── __init__.py
│   │   ├── engine.py           # Orchestrateur retrieval
│   │   ├── semantic.py         # Recherche vectorielle
│   │   ├── lexical.py          # BM25
│   │   ├── fusion.py           # Fusion des scores
│   │   └── rerank.py           # Reranking
│   │
│   ├── llm/                    # LLM providers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── litellm_provider.py # Wrapper LiteLLM
│   │
│   ├── agents/                 # Système d'agents V1
│   │   ├── __init__.py
│   │   ├── base.py             # Agent abstrait
│   │   ├── query_analyzer.py   # Agent analyse requête
│   │   └── response_generator.py # Agent réponse
│   │
│   ├── chatbot/                # Interface chatbot
│   │   ├── __init__.py
│   │   └── gradio_ui.py
│   │
│   ├── api/                    # REST API
│   │   ├── __init__.py
│   │   ├── app.py              # FastAPI app
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── query.py
│   │       └── health.py
│   │
│   ├── cli/                    # CLI commands
│   │   ├── __init__.py
│   │   ├── main.py             # Click/Typer app
│   │   ├── init.py
│   │   ├── ingest.py
│   │   ├── serve.py
│   │   └── query.py
│   │
│   └── utils/                  # Utilitaires
│       ├── __init__.py
│       ├── logging.py
│       └── async_utils.py
│
├── tests/                      # Tests
│   ├── __init__.py
│   ├── conftest.py             # Fixtures pytest
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_chunkers.py
│   │   └── ...
│   ├── integration/
│   │   ├── test_ingestion.py
│   │   ├── test_retrieval.py
│   │   └── ...
│   └── e2e/
│       └── test_full_pipeline.py
│
├── templates/                  # Templates de config
│   ├── minimal.yaml
│   ├── hybrid.yaml
│   └── full.yaml
│
├── examples/                   # Exemples d'utilisation
│   ├── quickstart/
│   └── advanced/
│
└── docs/                       # Documentation
    ├── getting-started.md
    ├── configuration.md
    └── api-reference.md
```

---

## 🔧 Conventions de Code

### Style
- **Formatter** : `ruff format`
- **Linter** : `ruff check`
- **Type hints** : Obligatoires partout
- **Docstrings** : Google style

### Patterns

```python
# Tous les composants suivent le pattern Provider
class BaseProvider(ABC):
    @abstractmethod
    async def process(self, input: InputModel) -> OutputModel:
        pass

# Factory pattern pour instanciation depuis config
def create_embedder(config: EmbeddingConfig) -> BaseEmbedder:
    match config.provider:
        case "openai":
            return OpenAIEmbedder(config)
        case "ollama":
            return OllamaEmbedder(config)
        case _:
            raise ValueError(f"Unknown provider: {config.provider}")
```

### Async
- Toutes les I/O sont async (LLM calls, vector store, API)
- Utiliser `asyncio.gather` pour parallélisation
- Timeouts explicites sur tous les appels externes

### Error Handling
```python
# Exceptions custom pour chaque module
class RAGKitError(Exception):
    """Base exception"""

class ConfigError(RAGKitError):
    """Configuration invalide"""

class IngestionError(RAGKitError):
    """Erreur d'ingestion"""

class RetrievalError(RAGKitError):
    """Erreur de retrieval"""
```

---

## 🧪 Stratégie de Test

### Niveaux de Test

| Niveau | Scope | Outils |
|--------|-------|--------|
| Unit | Fonctions isolées | pytest, pytest-asyncio |
| Integration | Composants ensemble | pytest, fixtures |
| E2E | Pipeline complet | pytest, docker-compose |

### Fixtures Standards

```python
# conftest.py
@pytest.fixture
def sample_config():
    return load_config("tests/fixtures/test_config.yaml")

@pytest.fixture
def sample_documents():
    return [
        Document(content="...", metadata={...}),
        ...
    ]

@pytest.fixture
async def vector_store(sample_config):
    store = create_vector_store(sample_config.vector_store)
    yield store
    await store.clear()
```

### Mocking
- LLM calls : toujours mockés en unit tests
- Vector store : in-memory ChromaDB pour tests rapides
- External APIs : `pytest-httpx` ou `respx`

---

## 📚 Ressources

### Documentation de Référence
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/)

### Inspirations Techniques
- [LlamaIndex Architecture](https://docs.llamaindex.ai/)
- [Haystack Pipelines](https://docs.haystack.deepset.ai/)
- [RAGAS Evaluation](https://docs.ragas.io/)

---

## 👥 Contact

Pour toute question sur ce document ou le projet :
- Créer une issue sur le repo
- Tag `@project-lead` pour questions d'architecture
