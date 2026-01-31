# RAGKIT Setup Mode - Specification

## Objectif

Permettre a RAGKIT de demarrer sans cles API ni configuration complete. L'UI est accessible immediatement et guide l'utilisateur a travers un wizard de configuration. Ajouter le support de nouveaux fournisseurs LLM/embedding (DeepSeek, Groq, Mistral) et traiter les providers locaux (Ollama) comme des citoyens de premier rang.

**Flux utilisateur cible :**

```
pip install ragkit
ragkit init my-project
cd my-project
ragkit serve
# Ouvrir http://localhost:8000 -> UI accessible, etat "non configure"
# Configurer via le wizard -> Apply -> le serveur redemarre en mode operationnel
```

---

## Situation actuelle (probleme)

Le serveur charge et valide la config au demarrage (`ragkit/cli/main.py:108-120`). La validation exige les cles pour les providers hosted (OpenAI, Cohere, Anthropic). Si une cle manque, le chargement echoue et le serveur ne demarre pas, donc l'UI n'est jamais accessible.

**Chaine de demarrage actuelle :**
```
CLI serve → ConfigLoader.load_with_env() → Pydantic validation → custom validators
→ create_embedder() → create_vector_store() → LLMRouter() → AgentOrchestrator()
→ create_app() → uvicorn.run()
```

Chaque etape depend de la precedente. Si `embedding` ou `llm` ne sont pas configures, tout echoue.

---

## Phase 1 : Schema - Rendre les sections lourdes optionnelles

**Fichier :** `ragkit/config/schema.py`

### 1.1 Champs optionnels sur `RAGKitConfig` (ligne 490)

Actuellement tous les 12 champs sont requis. Rendre optionnels les 5 qui necessitent des cles/config externe :

```python
class RAGKitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    project: ProjectConfig
    ingestion: IngestionConfig | None = None          # etait requis
    embedding: EmbeddingConfig | None = None           # etait requis
    vector_store: VectorStoreConfig = Field(default_factory=...)  # garde, a des defaults
    retrieval: RetrievalConfig | None = None           # etait requis
    llm: LLMConfig | None = None                       # etait requis
    agents: AgentsConfig | None = None                 # etait requis
    conversation: ConversationConfig = Field(default_factory=...)  # garde
    chatbot: ChatbotConfig = Field(default_factory=...)            # garde
    api: APIConfig = Field(default_factory=...)                    # garde
    observability: ObservabilityConfig = Field(default_factory=...)  # garde
```

### 1.2 Propriete `is_configured`

Ajouter sur `RAGKitConfig` :

```python
@property
def is_configured(self) -> bool:
    """Retourne True quand toutes les sections operationnelles sont presentes."""
    return all([
        self.ingestion is not None,
        self.embedding is not None,
        self.llm is not None,
        self.agents is not None,
        self.retrieval is not None,
    ])
```

### 1.3 Expansion des providers LLM

**Fichier :** `ragkit/config/schema.py` ligne 265

```python
# Avant
provider: Literal["openai", "anthropic", "ollama"]

# Apres
provider: Literal["openai", "anthropic", "ollama", "deepseek", "groq", "mistral"]
```

### 1.4 Expansion des providers embedding

**Fichier :** `ragkit/config/schema.py` ligne 110

```python
# Avant
provider: Literal["openai", "ollama", "cohere"]

# Apres
provider: Literal["openai", "ollama", "cohere", "litellm"]
```

Le provider `litellm` est un passe-plat generique : il delegue a `litellm.aembedding()` qui supporte DeepSeek, Mistral, etc. nativement.

### 1.5 Mise a jour des validators

**Fichier :** `ragkit/config/validators.py`

Les validators actuels accedent directement `config.retrieval`, `config.embedding`, `config.llm` (lignes 34-64). Si ces sections sont `None`, ca crash.

**Modification :** ajouter des gardes en debut de chaque bloc :

```python
def validate_config(config: RAGKitConfig) -> list[str]:
    errors: list[str] = []

    # Vector store validation (toujours present)
    # ... inchange ...

    # Retrieval validation
    if config.retrieval is not None:
        # ... validations existantes lignes 34-42 ...

    # Embedding / LLM key hints
    if config.embedding is not None:
        # ... validations existantes lignes 45-56 ...

    if config.llm is not None:
        # ... validations existantes lignes 58-60 ...

    return errors
```

---

## Phase 2 : CLI & Template setup

### 2.1 Template setup

**Fichier a creer :** `templates/setup.yaml`

YAML minimal sans sections operationnelles - uniquement les sections avec defaults :

```yaml
version: "1.0"

project:
  name: "ragkit-project"
  description: "My RAG project"
  environment: "development"

vector_store:
  provider: "chroma"
  chroma:
    mode: "memory"
    collection_name: "ragkit_documents"

api:
  enabled: true
  server:
    host: "0.0.0.0"
    port: 8000
  cors:
    enabled: true
    origins: ["*"]
  docs:
    enabled: true
```

Pas de section `ingestion`, `embedding`, `llm`, `agents`, `retrieval`. Elles seront configurees via le wizard UI.

### 2.2 Template par defaut

**Fichier :** `ragkit/cli/main.py` ligne 29

```python
# Avant
template: str = typer.Option("minimal", help="Template to use")

# Apres
template: str = typer.Option("setup", help="Template to use (setup, minimal, hybrid, full)")
```

### 2.3 Commande `serve` en mode setup

**Fichier :** `ragkit/cli/main.py` lignes 97-167

La commande `serve` doit gerer deux cas :

```python
@app.command()
def serve(
    config: Path = typer.Option("ragkit.yaml", "--config", "-c"),
    api_only: bool = typer.Option(False),
    chatbot_only: bool = typer.Option(False),
    with_ui: bool = typer.Option(False),
) -> None:
    loader = ConfigLoader()
    cfg = loader.load_with_env(config)  # ne crashe plus grace aux fields optionnels

    setup_mode = not cfg.is_configured

    if setup_mode:
        typer.echo("Starting in setup mode — configure via UI at http://...")
        # Ne pas creer embedder/llm/orchestrator
        orchestrator = None
        vector_store = None
        embedder = None
        llm_router = None
    else:
        # Chemin actuel : creer tous les composants
        embedder = create_embedder(cfg.embedding.query_model)
        vector_store = create_vector_store(cfg.vector_store)
        retrieval = RetrievalEngine(cfg.retrieval, vector_store, embedder)
        llm_router = LLMRouter(cfg.llm)
        orchestrator = AgentOrchestrator(cfg.agents, retrieval, llm_router, ...)

    if not chatbot_only:
        from ragkit.api.app import create_app
        app_instance = create_app(
            cfg, orchestrator,
            config_path=config,
            vector_store=vector_store,
            embedder=embedder,
            llm_router=llm_router,
            setup_mode=setup_mode,
        )
        # ... uvicorn.run comme avant ...
```

### 2.4 ConfigLoader tolerant

**Fichier :** `ragkit/config/loader.py` lignes 25-30

`load_with_env` doit tolerer les `_env` references quand la section parente est absente. Actuellement, `_resolve_env_vars` raise `ConfigError` si une variable d'environnement manque (ligne 60).

**Modification :** Ne resoudre les `_env` vars que pour les sections presentes. Si une section est `None`, elle n'a pas de sous-cles `api_key_env` a resoudre, donc pas de changement necessaire dans `_resolve_env_vars`. Par contre, `_raise_if_errors` (ligne 35) ne doit pas echouer pour les sections `None` - c'est gere par Phase 1.5.

---

## Phase 3 : App factory & gardes de routes

### 3.1 Signature `create_app`

**Fichier :** `ragkit/api/app.py` ligne 23

```python
# Avant
def create_app(
    config: RAGKitConfig,
    orchestrator: AgentOrchestrator,
    ...
) -> FastAPI:

# Apres
def create_app(
    config: RAGKitConfig,
    orchestrator: AgentOrchestrator | None = None,
    *,
    config_path: Path | None = None,
    vector_store: Any | None = None,
    embedder: Any | None = None,
    llm_router: Any | None = None,
    state_store: StateStore | None = None,
    metrics: MetricsCollector | None = None,
    setup_mode: bool = False,
) -> FastAPI:
```

Stocker le flag dans `app.state` :
```python
app.state.setup_mode = setup_mode
```

### 3.2 Endpoint `/api/status`

**Fichier a creer :** `ragkit/api/routes/status.py`

```python
@router.get("/api/status")
async def get_status(request: Request):
    config = request.app.state.config
    return {
        "configured": config.is_configured,
        "setup_mode": request.app.state.setup_mode,
        "version": config.version,
        "project": config.project.name,
        "components": {
            "embedding": config.embedding is not None,
            "llm": config.llm is not None,
            "agents": config.agents is not None,
            "retrieval": config.retrieval is not None,
            "ingestion": config.ingestion is not None,
            "vector_store": True,  # toujours present
        },
    }
```

Enregistrer dans `create_app` :
```python
from ragkit.api.routes.status import router as status_router
app.include_router(status_router)
```

### 3.3 Middleware de garde (mode setup)

Ajouter un middleware dans `create_app` qui bloque les routes operationnelles en mode setup :

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class SetupModeGuard(BaseHTTPMiddleware):
    BLOCKED_PREFIXES = ("/api/v1/query", "/api/v1/admin/ingestion")

    async def dispatch(self, request, call_next):
        if request.app.state.setup_mode:
            for prefix in self.BLOCKED_PREFIXES:
                if request.url.path.startswith(prefix):
                    return JSONResponse(
                        status_code=503,
                        content={"detail": "Server is in setup mode. Configure via the UI first."},
                    )
        return await call_next(request)

# Dans create_app :
if setup_mode:
    app.add_middleware(SetupModeGuard)
```

Routes qui restent accessibles en setup mode :
- `GET /api/status` - statut du serveur
- `GET/PUT /api/v1/admin/config` - lire/modifier la config
- `POST /api/v1/admin/config/validate` - valider
- `POST /api/v1/admin/config/apply` - appliquer (Phase 4)
- `GET /api/v1/admin/defaults` - defaults (Phase 7)
- `GET /api/v1/health/*` - health checks
- `/` (frontend statique)

### 3.4 Adaptation du health check

**Fichier :** `ragkit/api/routes/admin/health.py` lignes 57, 78, 96

Les fonctions `_check_llm_health`, `_check_embedding_health`, `_check_reranker_health` accedent directement `config.llm.primary`, `config.embedding.document_model`, `config.retrieval.rerank`. Si ces sections sont `None`, ca crash.

**Modification :** ajouter des gardes :

```python
def _check_llm_health(request: Request) -> ComponentHealth:
    if request.app.state.config.llm is None:
        return ComponentHealth(
            name="LLM Primary", status=ComponentStatus.UNKNOWN,
            last_check=datetime.now(timezone.utc),
            message="Not configured",
        )
    config = request.app.state.config.llm.primary
    # ... reste inchange ...
```

Idem pour `_check_embedding_health` et `_check_reranker_health`.

Et dans `get_detailed_health` (ligne 57) :
```python
if request.app.state.config.retrieval is not None and request.app.state.config.retrieval.rerank.enabled:
    components["reranker"] = _check_reranker_health(request)
```

---

## Phase 4 : Apply config & redemarrage serveur

### 4.1 Endpoint `POST /api/v1/admin/config/apply`

**Fichier :** `ragkit/api/routes/admin/config.py`

Ajouter un nouvel endpoint qui :
1. Valide la config complete (Pydantic + validators custom)
2. Verifie que `is_configured` est `True` sur la config validee
3. Sauvegarde le YAML sur disque
4. Declenche un redemarrage du serveur

```python
import os
import sys

@router.post("/apply")
async def apply_config(payload: ConfigUpdateRequest, request: Request):
    # Validation
    try:
        config = RAGKitConfig.model_validate(payload.config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"errors": [str(exc)]})

    if not config.is_configured:
        raise HTTPException(
            status_code=400,
            detail={"errors": ["Configuration incomplete — all sections must be filled"]},
        )

    errors = validate_custom(config)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    # Sauvegarder
    config_path: Path = request.app.state.config_path
    yaml_content = yaml.safe_dump(payload.config, sort_keys=False)
    config_path.write_text(yaml_content, encoding="utf-8")

    # Redemarre le processus
    # os.execv remplace le processus courant par un nouveau
    os.execv(sys.executable, [sys.executable] + sys.argv)
```

**Note importante :** `os.execv` fonctionne sur Linux/macOS. Sur Windows, utiliser `subprocess.Popen` + `sys.exit` :

```python
import platform

def _restart_server():
    if platform.system() == "Windows":
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    else:
        os.execv(sys.executable, [sys.executable] + sys.argv)
```

### 4.2 Distinction avec `PUT /config` existant

Le `PUT` existant (ligne 55) sauvegarde sans redemarrer. Il reste utile pour des changements mineurs (modifier un prompt, un threshold).

Le `POST /apply` est pour le passage de setup mode a operationnel, ou pour des changements structurels necessitant un redemarrage (changer de provider, ajouter un LLM).

---

## Phase 5 : Expansion des providers

### 5.1 LLM - prefix map

**Fichier :** `ragkit/llm/litellm_provider.py` ligne 111

La fonction `_resolve_model_name` gere actuellement `ollama` et `anthropic`. Avec les nouveaux providers, utiliser une map :

```python
# Providers qui necessitent un prefixe pour LiteLLM
_PROVIDER_PREFIXES: dict[str, str] = {
    "ollama": "ollama/",
    "anthropic": "anthropic/",
    "deepseek": "deepseek/",
    "groq": "groq/",
    "mistral": "mistral/",
    # openai n'a pas de prefixe (c'est le defaut de LiteLLM)
}

def _resolve_model_name(config: LLMModelConfig) -> str:
    if "/" in config.model:
        return config.model
    prefix = _PROVIDER_PREFIXES.get(config.provider, "")
    return f"{prefix}{config.model}"
```

### 5.2 Providers qui necessitent une cle API

Mettre a jour les validators et health checks pour reconnaitre les nouveaux providers qui necessitent une cle :

**`ragkit/config/validators.py` :**
```python
_HOSTED_LLM_PROVIDERS = {"openai", "anthropic", "deepseek", "groq", "mistral"}
_HOSTED_EMBEDDING_PROVIDERS = {"openai", "cohere"}

# Utiliser ces sets au lieu de hardcoder {"openai", "anthropic"} etc.
if config.llm.primary.provider in _HOSTED_LLM_PROVIDERS:
    if not config.llm.primary.api_key and not config.llm.primary.api_key_env:
        errors.append("llm.primary.api_key or api_key_env is required")
```

**`ragkit/api/routes/admin/health.py` :**
```python
_HOSTED_LLM_PROVIDERS = {"openai", "anthropic", "deepseek", "groq", "mistral"}

def _check_llm_health(request: Request) -> ComponentHealth:
    # ...
    if config.provider in _HOSTED_LLM_PROVIDERS:
        if not (config.api_key or config.api_key_env):
            # ...
```

### 5.3 LiteLLM Embedder

**Fichier a creer :** `ragkit/embedding/providers/litellm.py`

```python
"""LiteLLM-based embedder supporting any provider that LiteLLM handles."""

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder


class LiteLLMEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self._dimensions = config.params.dimensions

    @property
    def dimensions(self) -> int:
        if self._dimensions:
            return self._dimensions
        raise ValueError("dimensions must be set for litellm embedder")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import litellm
        response = await litellm.aembedding(
            model=self.config.model,
            input=texts,
            api_key=self.config.api_key,
        )
        return [item["embedding"] for item in response.data]

    async def embed_query(self, query: str) -> list[float]:
        result = await self.embed([query])
        return result[0]
```

### 5.4 Factory embedding

**Fichier :** `ragkit/embedding/__init__.py` ligne 13

Ajouter le cas `litellm` :

```python
from ragkit.embedding.providers.litellm import LiteLLMEmbedder

def create_embedder(config: EmbeddingModelConfig) -> BaseEmbedder:
    if config.provider == "openai":
        embedder: BaseEmbedder = OpenAIEmbedder(config)
    elif config.provider == "ollama":
        embedder = OllamaEmbedder(config)
    elif config.provider == "cohere":
        embedder = CohereEmbedder(config)
    elif config.provider == "litellm":
        embedder = LiteLLMEmbedder(config)
    else:
        raise ValueError(f"Unknown embedding provider: {config.provider}")
    # ... cache logic inchangee ...
```

---

## Phase 6 : Frontend - Mode setup

### 6.1 Hook `useStatus`

**Fichier a creer :** `ragkit-ui/src/hooks/useStatus.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { client } from '@/api/client';

interface ServerStatus {
  configured: boolean;
  setup_mode: boolean;
  version: string;
  project: string;
  components: Record<string, boolean>;
}

export function useStatus() {
  return useQuery<ServerStatus>({
    queryKey: ['status'],
    queryFn: () => client.get('/api/status').then((r) => r.data),
    refetchInterval: 10_000,
  });
}
```

### 6.2 Composant `SetupGuard`

**Fichier a creer :** `ragkit-ui/src/components/SetupGuard.tsx`

```tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useStatus } from '@/hooks/useStatus';

export function SetupGuard({ children }: { children: React.ReactNode }) {
  const { data: status, isLoading } = useStatus();
  const location = useLocation();

  if (isLoading) return null; // ou un spinner

  if (status?.setup_mode && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />;
  }

  return <>{children}</>;
}
```

### 6.3 Integration dans `App.tsx`

**Fichier :** `ragkit-ui/src/App.tsx`

```tsx
import { SetupGuard } from '@/components/SetupGuard';

export default function App() {
  return (
    <SetupGuard>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* ... routes inchangees ... */}
        </Route>
      </Routes>
    </SetupGuard>
  );
}
```

### 6.4 Wizard - nouveaux providers

**Fichier :** `ragkit-ui/src/components/wizard/steps/LLMStep.tsx`

Ajouter les options dans le `<Select>` :

```tsx
<option value="openai">OpenAI</option>
<option value="anthropic">Anthropic</option>
<option value="deepseek">DeepSeek</option>
<option value="groq">Groq</option>
<option value="mistral">Mistral</option>
<option value="ollama">Ollama (local)</option>
```

**Fichier :** `ragkit-ui/src/components/wizard/steps/EmbeddingStep.tsx`

```tsx
<option value="openai">OpenAI</option>
<option value="ollama">Ollama (local)</option>
<option value="cohere">Cohere</option>
<option value="litellm">LiteLLM (generic)</option>
```

### 6.5 Champ API key conditionnel

Dans `LLMStep.tsx` et `EmbeddingStep.tsx`, masquer le champ API key quand le provider est `ollama` :

```tsx
{primary.provider !== 'ollama' && (
  <div>
    <p className="text-sm font-semibold">API key</p>
    <Input placeholder="sk-..." value={primary.api_key || ''} onChange={...} />
  </div>
)}
```

### 6.6 Flow Apply & Restart

**Fichier :** `ragkit-ui/src/pages/Setup.tsx`

Remplacer `handleComplete` pour appeler `/apply` au lieu de `PUT /config` :

```typescript
const handleComplete = async () => {
  setError(null);
  setIsRestarting(false);

  try {
    await client.post('/api/v1/admin/config/apply', { config });
  } catch (err: any) {
    // Si le serveur coupe la connexion, c'est qu'il redemarre
    if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
      setIsRestarting(true);
      await waitForServer();
      navigate('/');
      return;
    }
    setError(err.response?.data?.detail?.errors?.join(', ') || 'Failed to apply configuration.');
    return;
  }

  // Si on arrive ici, le serveur n'a pas redemarre (ne devrait pas arriver)
  setIsRestarting(true);
  await waitForServer();
  navigate('/');
};

async function waitForServer(maxAttempts = 30, intervalMs = 2000) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await client.get('/api/status');
      if (res.data.configured) return;
    } catch {
      // serveur pas encore up
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error('Server did not restart in time');
}
```

### 6.7 Overlay de redemarrage

Ajouter un etat `isRestarting` et afficher un overlay :

```tsx
{isRestarting && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div className="rounded-2xl bg-white p-8 text-center shadow-xl">
      <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      <p className="text-lg font-medium">Restarting server...</p>
      <p className="mt-2 text-sm text-gray-500">Applying your configuration</p>
    </div>
  </div>
)}
```

### 6.8 Sidebar - indicateur setup

**Fichier :** `ragkit-ui/src/components/layout/Sidebar.tsx`

Ajouter un badge ou indicateur visuel quand `setup_mode` est actif :

```tsx
const { data: status } = useStatus();

{status?.setup_mode && (
  <div className="mx-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
    Setup required — configure your RAG pipeline
  </div>
)}
```

---

## Phase 7 : Defaults & prompts agents

### 7.1 Module defaults

**Fichier a creer :** `ragkit/config/defaults.py`

Fournir des configs par defaut sensees que le wizard peut pre-remplir :

```python
"""Sensible default configurations for setup mode."""

from ragkit.config.schema import (
    AgentsConfig, AgentsGlobalConfig,
    IngestionConfig, SourceConfig, ChunkingConfig, ParsingConfig, MetadataConfig,
    QueryAnalyzerConfig, QueryAnalyzerBehaviorConfig, QueryRewritingConfig,
    ResponseGeneratorConfig, ResponseBehaviorConfig,
    RetrievalConfig, SemanticRetrievalConfig,
)

def default_ingestion_config() -> IngestionConfig:
    return IngestionConfig(
        sources=[
            SourceConfig(type="local", path="./data/documents", patterns=["*.md", "*.txt", "*.pdf"])
        ],
        parsing=ParsingConfig(),
        chunking=ChunkingConfig(),
        metadata=MetadataConfig(extract=["source_path", "file_type"]),
    )

def default_retrieval_config() -> RetrievalConfig:
    return RetrievalConfig(
        architecture="semantic",
        semantic=SemanticRetrievalConfig(enabled=True, weight=1.0, top_k=10),
    )

def default_agents_config() -> AgentsConfig:
    return AgentsConfig(
        mode="default",
        query_analyzer=QueryAnalyzerConfig(
            llm="fast",
            behavior=QueryAnalyzerBehaviorConfig(
                detect_intents=["question", "greeting", "chitchat", "out_of_scope"],
                query_rewriting=QueryRewritingConfig(enabled=True, num_rewrites=1),
            ),
            system_prompt=(
                "You analyze user queries for a RAG system.\n"
                "Return JSON with intent, needs_retrieval, rewritten_query, reasoning."
            ),
            output_schema={
                "type": "object",
                "required": ["intent", "needs_retrieval"],
                "properties": {
                    "intent": {"type": "string"},
                    "needs_retrieval": {"type": "boolean"},
                    "rewritten_query": {"type": ["string", "null"]},
                    "reasoning": {"type": "string"},
                },
            },
        ),
        response_generator=ResponseGeneratorConfig(
            llm="primary",
            behavior=ResponseBehaviorConfig(),
            system_prompt=(
                "You answer using only the provided context.\n"
                "Cite sources using [Source: name].\n"
                "Context:\n{context}"
            ),
            no_retrieval_prompt="You are a friendly assistant. Answer briefly.",
            out_of_scope_prompt="Politely explain the question is outside the supported scope.",
        ),
        global_config=AgentsGlobalConfig(),
    )
```

### 7.2 Endpoint defaults

**Ajouter dans :** `ragkit/api/routes/admin/config.py` (ou nouveau fichier)

```python
from ragkit.config.defaults import (
    default_agents_config,
    default_ingestion_config,
    default_retrieval_config,
)

@router.get("/defaults")
async def get_defaults():
    return {
        "ingestion": default_ingestion_config().model_dump(),
        "retrieval": default_retrieval_config().model_dump(),
        "agents": default_agents_config().model_dump(by_alias=True),
    }
```

Le wizard frontend peut appeler cet endpoint pour pre-remplir les champs. L'utilisateur n'a plus qu'a choisir un provider + entrer sa cle API.

---

## Resume des fichiers

| Fichier | Action | Phase |
|---------|--------|-------|
| `ragkit/config/schema.py` | Edit : champs optionnels, `is_configured`, Literals elargis | 1 |
| `ragkit/config/validators.py` | Edit : gardes `None` sur sections, sets de providers | 1, 5 |
| `ragkit/config/loader.py` | Edit : tolerance config incomplete | 2 |
| `ragkit/config/defaults.py` | Creer : factories de config par defaut | 7 |
| `ragkit/cli/main.py` | Edit : template setup, serve en mode setup | 2 |
| `ragkit/api/app.py` | Edit : orchestrator optionnel, `setup_mode`, middleware | 3 |
| `ragkit/api/routes/status.py` | Creer : `GET /api/status` | 3 |
| `ragkit/api/routes/admin/config.py` | Edit : `POST /apply` avec redemarrage | 4 |
| `ragkit/api/routes/admin/health.py` | Edit : gardes `None` sur sections | 3 |
| `ragkit/llm/litellm_provider.py` | Edit : prefix map pour nouveaux providers | 5 |
| `ragkit/embedding/providers/litellm.py` | Creer : `LiteLLMEmbedder` | 5 |
| `ragkit/embedding/__init__.py` | Edit : cas `litellm` dans factory | 5 |
| `templates/setup.yaml` | Creer : template minimal | 2 |
| `ragkit-ui/src/hooks/useStatus.ts` | Creer : hook statut serveur | 6 |
| `ragkit-ui/src/components/SetupGuard.tsx` | Creer : redirection setup | 6 |
| `ragkit-ui/src/App.tsx` | Edit : wrapper `SetupGuard` | 6 |
| `ragkit-ui/src/pages/Setup.tsx` | Edit : flow apply + restart | 6 |
| `ragkit-ui/src/components/wizard/steps/LLMStep.tsx` | Edit : nouveaux providers, cle conditionnelle | 6 |
| `ragkit-ui/src/components/wizard/steps/EmbeddingStep.tsx` | Edit : nouveaux providers, cle conditionnelle | 6 |
| `ragkit-ui/src/components/layout/Sidebar.tsx` | Edit : badge setup mode | 6 |

### Tests a mettre a jour / creer

- `tests/unit/test_validators.py` : tester avec sections `None`
- `tests/unit/test_schema.py` : tester `is_configured`, config minimale
- `tests/unit/test_defaults.py` : tester les factories de defaults
- `tests/integration/test_admin_api.py` : tester `/apply`, `/defaults`, `/status`
- `tests/integration/test_setup_mode.py` : tester le middleware 503, acces admin OK en setup mode
- Tests existants : verifier qu'ils passent encore (certains creent des `RAGKitConfig` avec tous les champs - ils doivent continuer a marcher)

---

## Plan d'implementation detaille

### Graphe de dependances

```
Phase 1 (schema)
  |
  +---> Phase 2 (CLI/template)
  |       |
  |       +---> Phase 3 (app factory/gardes)
  |               |
  |               +---> Phase 4 (apply/restart)
  |               |       |
  |               |       +---> Phase 6 (frontend)
  |               |
  |               +---> Phase 7 (defaults)
  |                       |
  |                       +---> Phase 6 (frontend)
  |
  +---> Phase 5 (providers) -- independant, peut se faire en parallele de 2-3
```

---

### PHASE 1 : Schema (prerequis a toutes les autres phases)

#### Tache 1.1 — Rendre les champs optionnels sur RAGKitConfig

**Fichier :** `ragkit/config/schema.py`
**Lignes :** 490-505

**Etapes :**
1. Ouvrir `ragkit/config/schema.py`
2. Aux lignes 490-505, modifier la classe `RAGKitConfig` :
   - `ingestion: IngestionConfig` → `ingestion: IngestionConfig | None = None`
   - `embedding: EmbeddingConfig` → `embedding: EmbeddingConfig | None = None`
   - `retrieval: RetrievalConfig` → `retrieval: RetrievalConfig | None = None`
   - `llm: LLMConfig` → `llm: LLMConfig | None = None`
   - `agents: AgentsConfig` → `agents: AgentsConfig | None = None`
   - `vector_store: VectorStoreConfig` → `vector_store: VectorStoreConfig = Field(default_factory=_model_factory(VectorStoreConfig))`
   - `conversation: ConversationConfig` → `conversation: ConversationConfig = Field(default_factory=_model_factory(ConversationConfig))`
   - `chatbot: ChatbotConfig` → `chatbot: ChatbotConfig = Field(default_factory=_model_factory(ChatbotConfig))`
   - `api: APIConfig` → `api: APIConfig = Field(default_factory=_model_factory(APIConfig))`
   - `observability: ObservabilityConfig` → `observability: ObservabilityConfig = Field(default_factory=_model_factory(ObservabilityConfig))`
3. Ajouter la propriete `is_configured` (voir spec Phase 1.2)

**Verification :**
```python
# Dans un shell Python :
from ragkit.config.schema import RAGKitConfig, ProjectConfig
cfg = RAGKitConfig(version="1.0", project=ProjectConfig(name="test"))
assert cfg.ingestion is None
assert cfg.is_configured is False
assert cfg.vector_store is not None  # default
assert cfg.api.server.port == 8000   # default
```

**Attention :** Les templates existants (`minimal.yaml`, `hybrid.yaml`, `full.yaml`) fournissent toujours tous les champs. Ils doivent continuer a se charger normalement. Verifier avec :
```bash
python -c "from ragkit.config.loader import ConfigLoader; ConfigLoader().load(Path('templates/minimal.yaml'))"
```

#### Tache 1.2 — Elargir les Literals de providers

**Fichier :** `ragkit/config/schema.py`

**Etapes :**
1. Ligne 110 (`EmbeddingModelConfig.provider`) : ajouter `"litellm"` au Literal
2. Ligne 265 (`LLMModelConfig.provider`) : ajouter `"deepseek"`, `"groq"`, `"mistral"` au Literal

**Verification :**
```python
from ragkit.config.schema import LLMModelConfig, LLMParams
m = LLMModelConfig(provider="deepseek", model="deepseek-chat", api_key="test", params=LLMParams())
assert m.provider == "deepseek"
```

#### Tache 1.3 — Gardes None dans validators

**Fichier :** `ragkit/config/validators.py`
**Lignes :** 15-66

**Etapes :**
1. Ligne 34 : wrapper le bloc retrieval (lignes 34-42) dans `if config.retrieval is not None:`
2. Ligne 45 : wrapper le bloc embedding (lignes 45-56) dans `if config.embedding is not None:`
3. Ligne 58 : wrapper le bloc llm (lignes 58-60) dans `if config.llm is not None:`
4. Ligne 62 : wrapper le bloc rerank (lignes 62-64) dans `if config.retrieval is not None and ...`
5. Extraire les sets de providers hosted dans des constantes en haut du fichier :
   ```python
   _HOSTED_LLM_PROVIDERS = {"openai", "anthropic", "deepseek", "groq", "mistral"}
   _HOSTED_EMBEDDING_PROVIDERS = {"openai", "cohere"}
   ```
6. Remplacer les `{"openai", "anthropic"}` et `{"openai", "cohere"}` hardcodes par ces constantes

**Verification :**
```python
from ragkit.config.schema import RAGKitConfig, ProjectConfig
from ragkit.config.validators import validate_config
cfg = RAGKitConfig(version="1.0", project=ProjectConfig(name="test"))
errors = validate_config(cfg)
assert errors == []  # pas d'erreur quand les sections sont None
```

**Verification tests existants :**
```bash
pytest tests/unit/test_validators.py -v
```
Les tests existants construisent des `RAGKitConfig` complets — ils doivent toujours passer.

#### Tache 1.4 — Tests unitaires du schema

**Fichier a creer :** `tests/unit/test_schema_setup.py`

**Tests a ecrire :**
1. `test_minimal_config` — RAGKitConfig avec seulement `version` + `project`, verifie que les optionnels sont None et les defaults sont presents
2. `test_is_configured_false` — config minimale, `is_configured` retourne False
3. `test_is_configured_true` — config complete (style minimal.yaml), `is_configured` retourne True
4. `test_is_configured_partial` — 4 sections sur 5 presentes, retourne False
5. `test_new_llm_providers` — valider que `deepseek`, `groq`, `mistral` sont acceptes
6. `test_new_embedding_provider_litellm` — valider que `litellm` est accepte
7. `test_existing_templates_still_load` — charger `minimal.yaml`, `hybrid.yaml`, `full.yaml` via `RAGKitConfig.model_validate()`, verifier `is_configured is True`

**Verification :**
```bash
pytest tests/unit/test_schema_setup.py -v
```

---

### PHASE 2 : CLI & Template (depend de Phase 1)

#### Tache 2.1 — Creer le template setup

**Fichier a creer :** `templates/setup.yaml`

**Etapes :**
1. Creer le fichier avec le contenu YAML decrit dans la spec (Phase 2.1)
2. Seules les sections `version`, `project`, `vector_store`, `api` sont presentes

**Verification :**
```python
from ragkit.config.loader import ConfigLoader
from pathlib import Path
cfg = ConfigLoader().load(Path("templates/setup.yaml"))
assert cfg.is_configured is False
assert cfg.llm is None
assert cfg.vector_store.provider == "chroma"
```

#### Tache 2.2 — Changer le template par defaut dans `init`

**Fichier :** `ragkit/cli/main.py`
**Ligne :** 29

**Etapes :**
1. Changer `"minimal"` par `"setup"` dans le `typer.Option`

**Verification :**
```bash
# Dans un dossier temporaire :
cd /tmp && ragkit init test-project
cat test-project/ragkit.yaml  # doit etre le contenu de setup.yaml
rm -rf test-project
```

#### Tache 2.3 — Adapter la commande `serve` pour le mode setup

**Fichier :** `ragkit/cli/main.py`
**Lignes :** 97-167

**Etapes :**
1. Apres `cfg = loader.load_with_env(config)` (ligne 109), ajouter :
   ```python
   setup_mode = not cfg.is_configured
   ```
2. Wrapper la creation des composants (lignes 111-120) dans un `if not setup_mode:` / `else:`
   - Branche `else` : toutes les variables a `None`
3. Passer `setup_mode=setup_mode` a `create_app()` (la signature sera modifiee en Phase 3)
4. En mode setup, ne pas lancer le chatbot Gradio (skip le bloc `if not api_only:` lignes 156-167)

**Attention — point de blocage :** Cette tache ne peut pas etre verifiee end-to-end tant que Phase 3 (create_app) n'est pas faite. Mais le code peut etre ecrit.

**Verification partielle :**
```bash
# Apres Phase 3 :
cd /tmp && ragkit init test-project && cd test-project
ragkit serve --api-only
# Le serveur doit demarrer et afficher "Starting in setup mode"
# http://localhost:8000/api/status doit repondre
```

#### Tache 2.4 — ConfigLoader tolerant

**Fichier :** `ragkit/config/loader.py`
**Ligne :** 60

**Etapes :**
1. Dans `_resolve_env_vars`, la condition ligne 60 `if env_value is None: raise ConfigError(...)` pose probleme si une `_env` reference existe dans le YAML mais la variable d'environnement n'est pas definie. Mais dans `setup.yaml`, il n'y a PAS de `_env` references, donc pas de probleme direct.
2. Neanmoins, pour le cas ou un utilisateur edite manuellement son YAML et ajoute une section `llm` avec `api_key_env: "OPENAI_API_KEY"` sans avoir defini la variable : changer le `raise ConfigError` en un **warning log** + mettre `None` comme valeur. Ou bien laisser en l'etat et documenter que les `_env` vars doivent etre definies si utilisees.

**Decision recommandee :** laisser le comportement actuel (raise). La configuration via UI n'utilise pas `_env` — elle ecrit directement `api_key` dans le YAML. Le `_env` pattern est pour les deployments avances.

**Verification :**
```python
from ragkit.config.loader import ConfigLoader
from pathlib import Path
cfg = ConfigLoader().load_with_env(Path("templates/setup.yaml"))
assert cfg.is_configured is False  # charge sans erreur
```

---

### PHASE 3 : App factory & gardes de routes (depend de Phase 2)

#### Tache 3.1 — Modifier la signature de `create_app`

**Fichier :** `ragkit/api/app.py`
**Ligne :** 23

**Etapes :**
1. Changer `orchestrator: AgentOrchestrator` en `orchestrator: AgentOrchestrator | None = None`
2. Ajouter `setup_mode: bool = False` comme parametre keyword-only
3. Apres `app.state.llm_router = llm_router` (ligne 48), ajouter `app.state.setup_mode = setup_mode`

**Verification :**
```python
from ragkit.api.app import create_app
from ragkit.config.schema import RAGKitConfig, ProjectConfig
cfg = RAGKitConfig(version="1.0", project=ProjectConfig(name="test"))
app = create_app(cfg, setup_mode=True)
assert app.state.setup_mode is True
assert app.state.orchestrator is None
```

#### Tache 3.2 — Creer l'endpoint /api/status

**Fichier a creer :** `ragkit/api/routes/status.py`

**Etapes :**
1. Creer le fichier avec le routeur et l'endpoint (voir spec Phase 3.2)
2. Dans `ragkit/api/app.py`, importer et enregistrer le routeur :
   ```python
   from ragkit.api.routes.status import router as status_router
   app.include_router(status_router)
   ```
   L'ajouter apres les autres `include_router` (ligne 62), avant le mount statique (ligne 64)

**Verification :**
```bash
# Apres avoir demarre le serveur en setup mode :
curl http://localhost:8000/api/status
# Reponse attendue :
# {"configured": false, "setup_mode": true, "version": "1.0", "project": "ragkit-project", "components": {...}}
```

#### Tache 3.3 — Ajouter le middleware SetupModeGuard

**Fichier :** `ragkit/api/app.py`

**Etapes :**
1. Definir la classe `SetupModeGuard` dans le meme fichier (ou dans un `ragkit/api/middleware.py` separe)
2. Dans `create_app`, apres la configuration CORS (ligne 57), ajouter :
   ```python
   if setup_mode:
       app.add_middleware(SetupModeGuard)
   ```

**Routes bloquees en setup mode :**
- `/api/v1/query` — l'orchestrator est None, ca crasherait
- `/api/v1/admin/ingestion/run` — l'embedder et le vector_store pourraient etre None

**Routes autorisees en setup mode :**
- `/api/status`
- `/api/v1/admin/config` (GET, PUT)
- `/api/v1/admin/config/validate` (POST)
- `/api/v1/admin/config/apply` (POST) — Phase 4
- `/api/v1/admin/config/defaults` (GET) — Phase 7
- `/api/v1/admin/health/detailed` (GET)
- `/api/v1/admin/metrics/*` (GET)
- `/api/v1/admin/ingestion/status` (GET) — informatif, ok en setup
- `/health` (GET)
- `/` — frontend statique

**Attention :** Le middleware doit uniquement bloquer les routes qui ECRIVENT ou EXECUTENT des operations (query, ingestion/run), pas les routes de lecture. Utiliser des prefixes precis :
```python
BLOCKED_PREFIXES = ("/api/v1/query",)
BLOCKED_EXACT = set()

# Pour ingestion, bloquer seulement POST /run, pas GET /status :
async def dispatch(self, request, call_next):
    if request.app.state.setup_mode:
        path = request.url.path
        if any(path.startswith(p) for p in self.BLOCKED_PREFIXES):
            return JSONResponse(status_code=503, content={...})
        if path == "/api/v1/admin/ingestion/run" and request.method == "POST":
            return JSONResponse(status_code=503, content={...})
    return await call_next(request)
```

**Verification :**
```bash
# Serveur en setup mode :
curl -X POST http://localhost:8000/api/v1/query -d '{"query":"test"}'
# → 503 {"detail": "Server is in setup mode. Configure via the UI first."}

curl http://localhost:8000/api/v1/admin/config
# → 200 (config actuelle)
```

#### Tache 3.4 — Adapter les health checks pour les sections None

**Fichier :** `ragkit/api/routes/admin/health.py`

**Etapes :**
1. `_check_llm_health` (ligne 77) : ajouter `if request.app.state.config.llm is None:` en debut → retourner UNKNOWN "Not configured"
2. `_check_embedding_health` (ligne 95) : ajouter `if request.app.state.config.embedding is None:` en debut → retourner UNKNOWN "Not configured"
3. `_check_reranker_health` (ligne 113) : ajouter `if request.app.state.config.retrieval is None:` en debut → retourner UNKNOWN "Not configured"
4. `get_detailed_health` (ligne 57) : wrapper `config.retrieval.rerank.enabled` dans un check None :
   ```python
   if config.retrieval is not None and config.retrieval.rerank.enabled:
   ```

**Verification :**
```bash
curl http://localhost:8000/api/v1/admin/health/detailed
# En setup mode : tous les composants UNKNOWN sauf vector_store (qui est toujours present)
```

#### Tache 3.5 — Adapter la route query pour orchestrator optionnel

**Fichier :** `ragkit/api/routes/query.py`

Le helper `get_orchestrator` (reference dans les dependances Depends) accede `request.app.state.orchestrator`. Si orchestrator est None, il faut retourner une erreur claire.

**Etapes :**
1. Dans la fonction `get_orchestrator` (ou dans le endpoint directement), ajouter :
   ```python
   orchestrator = request.app.state.orchestrator
   if orchestrator is None:
       raise HTTPException(status_code=503, detail="Server is in setup mode")
   return orchestrator
   ```

Ceci est une double securite avec le middleware (Phase 3.3). Le middleware bloque deja `/api/v1/query`, mais si quelqu'un arrive a passer (par ex. le middleware est desactive), on a un fallback.

**Verification :** Deja couverte par le test du middleware (Tache 3.3).

#### Tache 3.6 — Tests d'integration setup mode

**Fichier a creer :** `tests/integration/test_setup_mode.py`

**Tests a ecrire :**
1. `test_status_endpoint_setup_mode` — GET /api/status retourne `{"configured": false, "setup_mode": true, ...}`
2. `test_status_endpoint_normal_mode` — GET /api/status retourne `{"configured": true, "setup_mode": false, ...}`
3. `test_query_blocked_in_setup_mode` — POST /api/v1/query retourne 503
4. `test_ingestion_run_blocked_in_setup_mode` — POST /api/v1/admin/ingestion/run retourne 503
5. `test_config_accessible_in_setup_mode` — GET /api/v1/admin/config retourne 200
6. `test_health_accessible_in_setup_mode` — GET /api/v1/admin/health/detailed retourne 200
7. `test_ingestion_status_accessible_in_setup_mode` — GET /api/v1/admin/ingestion/status retourne 200

**Fixture helper :** Creer une fonction `_make_setup_app()` qui construit une FastAPI app en setup mode :
```python
def _make_setup_app():
    cfg = RAGKitConfig(version="1.0", project=ProjectConfig(name="test"))
    return create_app(cfg, setup_mode=True, config_path=Path("ragkit.yaml"))
```

Et une `_make_normal_app()` qui charge une config complete (comme dans `test_admin_api.py`).

**Verification :**
```bash
pytest tests/integration/test_setup_mode.py -v
```

---

### PHASE 4 : Apply config & redemarrage (depend de Phase 3)

#### Tache 4.1 — Endpoint POST /apply

**Fichier :** `ragkit/api/routes/admin/config.py`

**Etapes :**
1. Ajouter les imports necessaires : `os`, `sys`, `platform`, `subprocess`
2. Creer la fonction helper `_restart_server()` qui gere Windows vs Unix (voir spec Phase 4.1)
3. Creer l'endpoint `@router.post("/apply")` (voir spec Phase 4.1)

**Attention — timing de reponse :**
Le `os.execv` / `subprocess.Popen + sys.exit` tue le processus. La reponse HTTP ne sera probablement jamais envoyee au client. C'est VOULU : le frontend detecte l'erreur reseau et lance le polling (Phase 6.6).

Cependant, pour etre plus propre, on peut envoyer la reponse AVANT de redemarrer :
```python
import asyncio

@router.post("/apply")
async def apply_config(payload: ConfigUpdateRequest, request: Request):
    # ... validation et sauvegarde ...

    # Planifier le restart apres un court delai
    # pour que la reponse HTTP soit envoyee
    async def _delayed_restart():
        await asyncio.sleep(0.5)
        _restart_server()

    asyncio.get_event_loop().create_task(_delayed_restart())
    return {"status": "restarting", "message": "Configuration applied. Server restarting..."}
```

**Verification :**
Test manuel :
```bash
# Demarrer en setup mode
ragkit serve --api-only

# Envoyer une config complete via curl
curl -X POST http://localhost:8000/api/v1/admin/config/apply \
  -H "Content-Type: application/json" \
  -d @templates/minimal.yaml  # (convertir en JSON d'abord)

# Le serveur doit redemarrer
# Apres ~2s, http://localhost:8000/api/status doit retourner configured: true
```

Test automatise (plus delicat car il faut tester un restart de process) :
- Tester la validation : envoyer une config incomplete → 400
- Tester la validation : envoyer une config invalide → 400
- Tester la sauvegarde : mocker `_restart_server`, verifier que le YAML est ecrit sur disque

#### Tache 4.2 — Tests du endpoint apply

**Fichier :** `tests/integration/test_admin_api.py` (ajouter aux tests existants)

**Tests a ecrire :**
1. `test_apply_incomplete_config` — POST /apply avec config sans `llm` → 400
2. `test_apply_invalid_config` — POST /apply avec config invalide (mauvais provider) → 400
3. `test_apply_valid_config_saves_yaml` — POST /apply avec config complete, mocker `_restart_server`, verifier que le fichier YAML est ecrit avec le bon contenu (utiliser `tmp_path`)
4. `test_apply_calls_restart` — POST /apply, mocker `_restart_server`, verifier qu'il est appele

---

### PHASE 5 : Expansion des providers (depend de Phase 1, independant des Phases 2-4)

#### Tache 5.1 — Prefix map LiteLLM

**Fichier :** `ragkit/llm/litellm_provider.py`
**Lignes :** 111-116

**Etapes :**
1. Remplacer la fonction `_resolve_model_name` par la version avec prefix map (voir spec Phase 5.1)
2. Definir `_PROVIDER_PREFIXES` en constante de module

**Verification :**
```python
from ragkit.config.schema import LLMModelConfig, LLMParams
from ragkit.llm.litellm_provider import _resolve_model_name

# OpenAI : pas de prefixe
cfg = LLMModelConfig(provider="openai", model="gpt-4o-mini", params=LLMParams())
assert _resolve_model_name(cfg) == "gpt-4o-mini"

# DeepSeek : prefixe
cfg = LLMModelConfig(provider="deepseek", model="deepseek-chat", params=LLMParams())
assert _resolve_model_name(cfg) == "deepseek/deepseek-chat"

# Slash deja present : pas de prefixe ajoute
cfg = LLMModelConfig(provider="ollama", model="ollama/llama3", params=LLMParams())
assert _resolve_model_name(cfg) == "ollama/llama3"

# Groq
cfg = LLMModelConfig(provider="groq", model="llama-3.1-70b-versatile", params=LLMParams())
assert _resolve_model_name(cfg) == "groq/llama-3.1-70b-versatile"
```

#### Tache 5.2 — Creer LiteLLMEmbedder

**Fichier a creer :** `ragkit/embedding/providers/litellm.py`

**Etapes :**
1. Creer le fichier avec la classe `LiteLLMEmbedder` (voir spec Phase 5.3)
2. Verifier que `ragkit/embedding/providers/__init__.py` existe (ou le creer si necessaire)

**Verification :**
```python
# Test unitaire avec monkeypatch sur litellm.aembedding
```

#### Tache 5.3 — Mettre a jour la factory embedding

**Fichier :** `ragkit/embedding/__init__.py`

**Etapes :**
1. Ajouter l'import `from ragkit.embedding.providers.litellm import LiteLLMEmbedder`
2. Ajouter le `elif config.provider == "litellm":` dans `create_embedder`
3. Ajouter `"LiteLLMEmbedder"` dans `__all__`

**Verification :**
```python
from ragkit.config.schema import EmbeddingModelConfig, EmbeddingParams
from ragkit.embedding import create_embedder
cfg = EmbeddingModelConfig(
    provider="litellm", model="mistral/mistral-embed",
    api_key="test", params=EmbeddingParams(dimensions=1024)
)
embedder = create_embedder(cfg)
assert type(embedder).__name__ == "LiteLLMEmbedder"
```

#### Tache 5.4 — Mettre a jour les hosted providers dans validators et health

**Fichiers :**
- `ragkit/config/validators.py` — utiliser `_HOSTED_LLM_PROVIDERS` (deja fait en Tache 1.3)
- `ragkit/api/routes/admin/health.py` — utiliser les memes sets dans `_check_llm_health` et `_check_embedding_health`

**Etapes :**
1. Dans `health.py`, definir les memes constantes qu'en validators ou les importer
2. Remplacer `{"openai", "anthropic"}` (ligne 79) par `_HOSTED_LLM_PROVIDERS`
3. Remplacer `{"openai", "cohere"}` (ligne 97) par `_HOSTED_EMBEDDING_PROVIDERS`

#### Tache 5.5 — Tests unitaires providers

**Fichier a creer :** `tests/unit/test_providers.py`

**Tests a ecrire :**
1. `test_resolve_model_name_openai` — pas de prefixe
2. `test_resolve_model_name_deepseek` — prefixe `deepseek/`
3. `test_resolve_model_name_groq` — prefixe `groq/`
4. `test_resolve_model_name_mistral` — prefixe `mistral/`
5. `test_resolve_model_name_ollama` — prefixe `ollama/`
6. `test_resolve_model_name_with_slash` — slash deja present, pas de double prefixe
7. `test_litellm_embedder_creation` — creer un LiteLLMEmbedder, verifier dimensions
8. `test_litellm_embedder_embed` — monkeypatch `litellm.aembedding`, verifier le retour
9. `test_create_embedder_litellm` — factory retourne LiteLLMEmbedder

**Verification :**
```bash
pytest tests/unit/test_providers.py -v
```

---

### PHASE 7 : Defaults (depend de Phase 3 pour l'endpoint, mais le module Python est independant)

#### Tache 7.1 — Creer le module defaults

**Fichier a creer :** `ragkit/config/defaults.py`

**Etapes :**
1. Creer le fichier avec les fonctions `default_ingestion_config()`, `default_retrieval_config()`, `default_agents_config()` (voir spec Phase 7.1)

**Verification :**
```python
from ragkit.config.defaults import default_agents_config, default_retrieval_config
agents = default_agents_config()
assert agents.query_analyzer.llm == "fast"
ret = default_retrieval_config()
assert ret.architecture == "semantic"
```

#### Tache 7.2 — Endpoint GET /defaults

**Fichier :** `ragkit/api/routes/admin/config.py`

**Etapes :**
1. Ajouter l'import des fonctions de defaults
2. Ajouter l'endpoint `@router.get("/defaults")` (voir spec Phase 7.2)

**Verification :**
```bash
curl http://localhost:8000/api/v1/admin/config/defaults
# → JSON avec ingestion, retrieval, agents defaults
```

#### Tache 7.3 — Tests unitaires defaults

**Fichier a creer :** `tests/unit/test_defaults.py`

**Tests a ecrire :**
1. `test_default_ingestion_config` — retourne une IngestionConfig valide avec source local
2. `test_default_retrieval_config` — retourne une RetrievalConfig semantic
3. `test_default_agents_config` — retourne une AgentsConfig avec prompts remplis
4. `test_defaults_pass_validation` — construire une RAGKitConfig complete en utilisant les defaults + un LLMConfig/EmbeddingConfig fictifs, verifier que `validate_config()` retourne aucune erreur

**Verification :**
```bash
pytest tests/unit/test_defaults.py -v
```

---

### PHASE 6 : Frontend (depend de Phases 3, 4, 5, 7)

#### Tache 6.1 — Fonction API `applyConfig` + `fetchStatus`

**Fichier :** `ragkit-ui/src/api/config.ts`

**Etapes :**
1. Ajouter la fonction `applyConfig(config)` qui fait un `POST /api/v1/admin/config/apply`
2. Ajouter la fonction `fetchStatus()` qui fait un `GET /api/status`

**Fichier :** `ragkit-ui/src/api/client.ts` — inchange (le client axios existant suffit)

#### Tache 6.2 — Hook useStatus

**Fichier a creer :** `ragkit-ui/src/hooks/useStatus.ts`

**Etapes :**
1. Creer le hook avec TanStack Query (voir spec Phase 6.1)
2. `refetchInterval: 10_000` pour polling toutes les 10s

#### Tache 6.3 — Composant SetupGuard

**Fichier a creer :** `ragkit-ui/src/components/SetupGuard.tsx`

**Etapes :**
1. Creer le composant (voir spec Phase 6.2)
2. Utilise `useStatus()` pour determiner si le serveur est en setup mode
3. Redirige vers `/setup` si `setup_mode && path !== '/setup'`

#### Tache 6.4 — Integrer SetupGuard dans App.tsx

**Fichier :** `ragkit-ui/src/App.tsx`

**Etapes :**
1. Importer `SetupGuard`
2. Wrapper le composant `<Routes>` avec `<SetupGuard>`

**Attention :** Le `SetupGuard` doit etre a l'INTERIEUR du `<BrowserRouter>` (fourni par le parent) car il utilise `useLocation`. Verifier le point de montage du Router dans `main.tsx`.

#### Tache 6.5 — Mettre a jour les options providers dans le wizard

**Fichiers :**
- `ragkit-ui/src/components/wizard/steps/LLMStep.tsx`
- `ragkit-ui/src/components/wizard/steps/EmbeddingStep.tsx`

**Etapes pour LLMStep.tsx :**
1. Ajouter les `<option>` pour DeepSeek, Groq, Mistral (voir spec Phase 6.4)
2. Rendre le champ API key conditionnel : masquer si `provider === 'ollama'` (voir spec Phase 6.5)
3. Ajouter un placeholder dynamique pour le model selon le provider :
   - openai → `"gpt-4o-mini"`
   - anthropic → `"claude-sonnet-4-20250514"`
   - deepseek → `"deepseek-chat"`
   - groq → `"llama-3.1-70b-versatile"`
   - mistral → `"mistral-large-latest"`
   - ollama → `"llama3"`

**Etapes pour EmbeddingStep.tsx :**
1. Ajouter `<option value="litellm">LiteLLM (generic)</option>`
2. Masquer le champ API key si `provider === 'ollama'`
3. Placeholder dynamique pour le model :
   - openai → `"text-embedding-3-large"`
   - ollama → `"nomic-embed-text"`
   - cohere → `"embed-multilingual-v3.0"`
   - litellm → `"mistral/mistral-embed"`

#### Tache 6.6 — Flow Apply & Restart dans Setup.tsx

**Fichier :** `ragkit-ui/src/pages/Setup.tsx`

**Etapes :**
1. Ajouter l'etat `isRestarting` :
   ```typescript
   const [isRestarting, setIsRestarting] = useState(false);
   ```
2. Remplacer `handleComplete` pour appeler `applyConfig` au lieu de `updateConfig` (voir spec Phase 6.6)
3. Ajouter la fonction `waitForServer` (voir spec Phase 6.6)
4. Ajouter l'overlay de redemarrage (voir spec Phase 6.7)
5. Avant le `applyConfig`, pre-remplir les sections manquantes avec les defaults :
   - Appeler `GET /api/v1/admin/config/defaults`
   - Merger les defaults avec la config du wizard (les choix de l'utilisateur ecrasent les defaults)
   - Envoyer la config complete a `/apply`

**Attention — merge des defaults :**
L'utilisateur configure via le wizard : provider LLM, model, API key, provider embedding, model, API key, et eventuellement les sources. Les sections `agents`, `retrieval`, `ingestion` doivent etre pre-remplies avec les defaults du backend.

```typescript
const handleComplete = async () => {
  // 1. Fetch defaults
  const { data: defaults } = await apiClient.get('/api/v1/admin/config/defaults');

  // 2. Merge : wizard config ecrase les defaults
  const fullConfig = {
    ...config,  // wizard config (project, llm, embedding, eventuellement sources)
    ingestion: config.ingestion || defaults.ingestion,
    retrieval: config.retrieval || defaults.retrieval,
    agents: config.agents || defaults.agents,
  };

  // 3. Apply
  try {
    await applyConfig(fullConfig);
  } catch ...
};
```

#### Tache 6.7 — Badge setup dans la Sidebar

**Fichier :** `ragkit-ui/src/components/layout/Sidebar.tsx`

**Etapes :**
1. Importer `useStatus`
2. Ajouter le bloc conditionnel (voir spec Phase 6.8)

#### Tache 6.8 — Verification frontend complete

**Scenario de test manuel :**
1. `ragkit init test-project && cd test-project`
2. `ragkit serve --api-only`
3. Ouvrir `http://localhost:8000` dans le navigateur
4. Verifier : redirection automatique vers `/setup`
5. Remplir le wizard : project name, choisir Ollama comme LLM provider, model "llama3"
6. Choisir Ollama comme embedding provider, model "nomic-embed-text"
7. Laisser les sources par defaut
8. Cliquer "Apply"
9. Verifier : overlay "Restarting server..."
10. Apres redemarrage : redirection vers le dashboard
11. Verifier : `/api/status` retourne `configured: true, setup_mode: false`
12. Verifier : le wizard n'est plus force (on peut naviguer librement)

---

### Verification globale post-implementation

```bash
# 1. Tests unitaires
pytest tests/unit/ -v

# 2. Tests integration
pytest tests/integration/ -v

# 3. Tous les tests
pytest -v

# 4. Type checking
pyright ragkit/

# 5. Linting
ruff check ragkit/ tests/

# 6. Test E2E manuel — parcours complet
ragkit init e2e-test
cd e2e-test
ragkit serve --api-only
# → Ouvrir UI, configurer, apply, verifier redemarrage
```

### Risques et points d'attention

| Risque | Impact | Mitigation |
|--------|--------|------------|
| `os.execv` ne fonctionne pas sur Windows | Restart casse sur Windows | Utiliser `subprocess.Popen` + `sys.exit` sur Windows (voir Phase 4.1) |
| Tests existants qui construisent `RAGKitConfig(...)` complet | Regression si la signature change | Les champs optionnels ont des defaults `None` — les tests qui passent tous les champs ne sont pas impactes |
| Le middleware bloque trop de routes | L'admin ne peut plus configurer en setup mode | Utiliser une allowlist de prefixes bloques plutot qu'une blocklist. Tester chaque route admin en setup mode |
| Le frontend appelle `/apply` mais la reponse n'arrive jamais (le process meurt) | Le frontend croit que ca a echoue | Detecter `ERR_NETWORK` comme un signal de redemarrage, puis poll `/api/status` |
| Config YAML corrompue apres sauvegarde | Le serveur ne redemarre plus | Valider la config COMPLETEMENT avant de sauvegarder. Garder un backup du YAML precedent (`ragkit.yaml.bak`) avant ecriture |
| L'utilisateur navigue manuellement a une route bloquee | 503 JSON au lieu d'une page d'erreur | Le `SetupGuard` frontend empeche la navigation. Le middleware backend est un filet de securite |
