# RAGKIT - Backend Test Procedure

Procedure de validation complete du backend ragkit.
Tous les tests se font via CLI et appels HTTP (curl), sans frontend.

---

## Environnement de test

| Element | Chemin |
|---------|--------|
| **Repertoire de travail** | `C:\Users\henri\Projets\test_ragkit` |
| **Code source ragkit** | `C:\Users\henri\Projets\ragkit` |
| **Base de connaissances** | `C:\Users\henri\Projets\Branham\sermons\1947` |
| **Fichier .env (cles API)** | `C:\Users\henri\Projets\test_ragkit\.env` |

> Toutes les commandes de cette procedure doivent etre executees depuis le
> repertoire de travail `C:\Users\henri\Projets\test_ragkit` sauf indication
> contraire.

### Base de connaissances de reference

Le dossier `C:\Users\henri\Projets\Branham\sermons\1947` contient 6 fichiers
de sermons (3 `.pdf`, 3 `.doc`) en francais, totalisant environ 36 000 mots.
Ce corpus produit environ 539 chunks avec la configuration par defaut
(chunking fixe, 512 tokens, overlap 50).

---

## Pre-requis

### Outils necessaires

- Python 3.10+
- curl
- jq (optionnel, pour formater le JSON)
- antiword (pour le support `.doc`, optionnel)

### Cles API

Le fichier `.env` doit exister dans `C:\Users\henri\Projets\test_ragkit`
avec les cles suivantes :

```
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
```

> Verifier qu'il n'y a pas de retour chariot `\r` dans le fichier (probleme courant
> sous Windows). Pour nettoyer : `sed -i 's/\r$//' .env`

### Documents de test

La base de connaissances de reference est :

```
C:\Users\henri\Projets\Branham\sermons\1947
```

Ce dossier contient :
- 3 fichiers `.pdf` (sermons en francais)
- 3 fichiers `.doc` (ancien format Word, sermons en francais)

Le corpus genere environ 539 chunks. Si vous utilisez un autre corpus, il doit
contenir au minimum :
- 2 fichiers `.pdf` avec du texte extractible
- (optionnel) 1-2 fichiers `.doc` ou `.docx`
- Assez de contenu pour generer au moins 50 chunks (~10 pages de texte)

---

## Phase 0 - Installation

### 0.1 Se placer dans le repertoire de test

```bash
cd C:\Users\henri\Projets\test_ragkit
```

### 0.2 Installer ragkit depuis le code source

```bash
pip install -e "C:\Users\henri\Projets\ragkit[dev]"
```

### 0.3 Verifier l'installation

```bash
ragkit --help
```

**PASS** : La commande affiche l'aide avec les sous-commandes `init`, `validate`,
`ingest`, `query`, `serve`, `ui`.

---

## Phase 1 - Initialisation du projet

### 1.1 Creer un projet avec le template minimal

Depuis `C:\Users\henri\Projets\test_ragkit` :

```bash
ragkit init mon-projet --template minimal
```

**PASS** : Un dossier `mon-projet/` est cree contenant :
- `ragkit.yaml`
- `data/documents/` (dossier vide)

### 1.2 Tester l'init avec un nom deja existant

```bash
ragkit init mon-projet
```

**PASS** : Erreur explicite `Destination already exists: mon-projet`.

### 1.3 Tester l'init avec un template inconnu

```bash
ragkit init autre-projet --template inexistant
```

**PASS** : Erreur explicite `Unknown template: inexistant`.

> Nettoyage : `rm -rf mon-projet autre-projet` (ces dossiers ne servent que
> pour cette phase).

---

## Phase 2 - Configuration

### 2.1 Ecrire le fichier ragkit.yaml

Creer `ragkit.yaml` dans `C:\Users\henri\Projets\test_ragkit` :

```yaml
version: "1.0"

project:
  name: "ragkit-test"
  description: "Projet de test backend ragkit"
  environment: "development"

ingestion:
  sources:
    - type: "local"
      path: "C:\\Users\\henri\\Projets\\Branham\\sermons\\1947"
      patterns:
        - "*.pdf"
        - "*.txt"
        - "*.md"
        - "*.doc"
        - "*.docx"
      recursive: true
  parsing:
    engine: "auto"
    ocr:
      enabled: false
      engine: "tesseract"
      languages: ["eng"]
  chunking:
    strategy: "fixed"
    fixed:
      chunk_size: 512
      chunk_overlap: 50
    semantic:
      similarity_threshold: 0.85
      min_chunk_size: 100
      max_chunk_size: 1000
      embedding_model: "document_model"
  metadata:
    extract: ["source_path", "file_type"]
    custom: {}

embedding:
  document_model:
    provider: "openai"
    model: "text-embedding-3-small"
    api_key_env: "OPENAI_API_KEY"
    params:
      batch_size: 100
      dimensions: null
    cache:
      enabled: false
      backend: "memory"
  query_model:
    provider: "openai"
    model: "text-embedding-3-small"
    api_key_env: "OPENAI_API_KEY"
    params:
      batch_size: 100
      dimensions: null
    cache:
      enabled: false
      backend: "memory"

vector_store:
  provider: "chroma"
  qdrant:
    mode: "memory"
    path: "./data/qdrant"
    collection_name: "ragkit_documents"
    distance_metric: "cosine"
  chroma:
    mode: "persistent"
    path: "./data/chroma"
    collection_name: "ragkit_test"

retrieval:
  architecture: "semantic"
  semantic:
    enabled: true
    weight: 1.0
    top_k: 10
    similarity_threshold: 0.0
  lexical:
    enabled: false
    weight: 0.0
    top_k: 10
    algorithm: "bm25"
    params:
      k1: 1.5
      b: 0.75
    preprocessing:
      lowercase: true
      remove_stopwords: true
      stopwords_lang: "english"
      stemming: false
  rerank:
    enabled: false
    provider: "none"
    model: null
    top_n: 5
    candidates: 20
    relevance_threshold: 0.0
  fusion:
    method: "weighted_sum"
    normalize_scores: true
    rrf_k: 60
  context:
    max_chunks: 5
    max_tokens: 3000
    deduplication:
      enabled: true
      similarity_threshold: 0.95

llm:
  primary:
    provider: "deepseek"
    model: "deepseek-chat"
    api_key_env: "DEEPSEEK_API_KEY"
    params:
      temperature: 0.7
      max_tokens: 1000
      top_p: 0.95
    timeout: 60
    max_retries: 3
  secondary: null
  fast:
    provider: "deepseek"
    model: "deepseek-chat"
    api_key_env: "DEEPSEEK_API_KEY"
    params:
      temperature: 0.3
      max_tokens: 300
      top_p: 0.9

agents:
  mode: "default"
  query_analyzer:
    llm: "fast"
    behavior:
      always_retrieve: false
      detect_intents: ["question", "greeting", "chitchat", "out_of_scope", "clarification"]
      query_rewriting:
        enabled: true
        num_rewrites: 1
    system_prompt: |
      You analyze user queries for a RAG system.
      Return JSON with intent, needs_retrieval, rewritten_query, reasoning.
    output_schema:
      type: "object"
      required: ["intent", "needs_retrieval"]
      properties:
        intent:
          type: "string"
          enum: ["question", "greeting", "chitchat", "out_of_scope", "clarification"]
        needs_retrieval:
          type: "boolean"
        rewritten_query:
          type: ["string", "null"]
        reasoning:
          type: "string"
  response_generator:
    llm: "primary"
    behavior:
      cite_sources: true
      citation_format: "[Source: {source_name}]"
      admit_uncertainty: true
      uncertainty_phrase: "I could not find relevant information in the documents."
      max_response_length: null
      response_language: "auto"
    system_prompt: |
      You answer using only the provided context.
      Cite sources using [Source: name].
      Context:
      {context}
    no_retrieval_prompt: |
      You are a friendly assistant. Answer briefly.
    out_of_scope_prompt: |
      Politely explain the question is outside the supported scope.
  global:
    timeout: 60
    max_retries: 2
    retry_delay: 1
    verbose: false

conversation:
  memory:
    enabled: true
    type: "buffer_window"
    window_size: 10
    include_in_prompt: true
  persistence:
    enabled: false
    backend: "memory"

chatbot:
  enabled: false
  type: "gradio"
  server:
    host: "0.0.0.0"
    port: 8080
    share: false
  ui:
    title: "RAGKIT Test"
    description: "Test assistant"
    theme: "soft"
    placeholder: "Ask a question..."
    examples: []
  features:
    show_sources: true
    show_latency: true
    streaming: false
    allow_feedback: false
    allow_export: false

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
    path: "/docs"
  streaming:
    enabled: false
    type: "sse"

observability:
  logging:
    level: "DEBUG"
    format: "text"
    file:
      enabled: false
      path: "./logs/ragkit.log"
      rotation: "daily"
      retention_days: 7
  metrics:
    enabled: true
    track: ["query_count", "query_latency"]
```

### 2.2 Valider la configuration

Depuis `C:\Users\henri\Projets\test_ragkit` (le `.env` est charge automatiquement) :

```bash
ragkit validate --config ragkit.yaml
```

**PASS** : Affiche `Configuration OK` sans erreur.

> Note : ragkit charge automatiquement le fichier `.env` situe a cote de
> `ragkit.yaml` (grace a `python-dotenv`). Pas besoin d'exporter manuellement.

### 2.3 Valider avec une cle API manquante

Renommer temporairement le `.env` pour simuler l'absence de cles :

```bash
mv .env .env.bak
ragkit validate --config ragkit.yaml
```

**PASS** : Erreur explicite `Missing environment variable: OPENAI_API_KEY`.

Restaurer :

```bash
mv .env.bak .env
```

### 2.4 Valider avec un YAML invalide

Creer un fichier `bad.yaml` contenant `version: "1.0"` sans `project:` puis :

```bash
ragkit validate --config bad.yaml
```

**PASS** : Erreur de validation Pydantic (champ `project` requis).

---

## Phase 3 - Ingestion via CLI

### 3.1 Nettoyer les donnees precedentes

```bash
rm -rf data/chroma .ragkit
```

### 3.2 Lancer l'ingestion

```bash
ragkit ingest --config ragkit.yaml
```

**PASS** : Le resultat affiche :
- `documents_loaded` = 6 (3 PDF + 3 DOC)
- `documents_parsed` = 6
- `chunks_created` ~ 539 (peut varier legerement selon la version des parsers)
- `chunks_embedded` = `chunks_created`
- `chunks_stored` = `chunks_embedded`
- `errors` = 0

> **Noter** les valeurs exactes pour comparaison avec l'ingestion API plus tard.
> Valeurs de reference : `documents_loaded=6 documents_parsed=6 chunks_created=539
> chunks_embedded=539 chunks_stored=539 errors=0`

### 3.3 Verifier l'ingestion incrementale

```bash
ragkit ingest --config ragkit.yaml --incremental
```

**PASS** : Le resultat affiche `documents_skipped` = nombre total de documents
(aucun fichier n'a ete modifie, donc tout est saute).

### 3.4 Tester l'ingestion avec un dossier vide

Modifier temporairement `ragkit.yaml` pour pointer vers un dossier vide, puis :

```bash
ragkit ingest --config ragkit.yaml
```

**PASS** : `documents_loaded=0`, pas d'erreur.

---

## Phase 4 - Query via CLI

### 4.1 Question simple liee aux documents

```bash
ragkit query "Resumer le contenu du premier document" --config ragkit.yaml
```

**PASS** :
- La reponse fait reference au contenu reel des documents
- Pas d'erreur Python (des warnings Pydantic sont acceptables)

### 4.2 Question de salutation

```bash
ragkit query "Bonjour!" --config ragkit.yaml
```

**PASS** : Reponse de salutation, pas de retrieval (reponse courte et amicale).

---

## Phase 5 - Demarrage du serveur

### 5.1 Demarrer le serveur API

```bash
ragkit serve --config ragkit.yaml --api-only --no-ui &
SERVER_PID=$!
sleep 8
```

### 5.2 Verifier que le serveur repond

```bash
curl -s http://localhost:8000/health
```

**PASS** : `{"status":"ok"}`

Si le serveur ne repond pas apres 15 secondes, c'est un **FAIL**.

---

## Phase 6 - Endpoint Health & Status

### 6.1 GET /health

```bash
curl -s http://localhost:8000/health
```

**PASS** :
- HTTP 200
- Body contient `{"status":"ok"}`

### 6.2 GET /api/status

```bash
curl -s http://localhost:8000/api/status
```

**PASS** :
- HTTP 200
- `configured` = `true`
- `setup_mode` = `false`
- `components` contient `embedding`, `llm`, `agents`, `retrieval`, `ingestion`,
  `vector_store` tous a `true`

### 6.3 GET /api/v1/admin/health/detailed

```bash
curl -s http://localhost:8000/api/v1/admin/health/detailed
```

**PASS** :
- HTTP 200
- `components.vector_store.status` = `"healthy"`
- `components.vector_store.latency_ms` est un nombre > 0
- Le champ `checked_at` est une date ISO 8601

> Note : Si `api.health.active_checks: true` dans ragkit.yaml, les composants
> `llm` et `embedding` affichent `"healthy"` ou `"unhealthy"` avec un temps de
> reponse. Sinon, ils affichent `"unknown"` (checks actifs desactives par defaut
> pour eviter des couts API).

---

## Phase 7 - Endpoints de configuration

### 7.1 GET /api/v1/admin/config

```bash
curl -s http://localhost:8000/api/v1/admin/config
```

**PASS** :
- HTTP 200
- Le body contient un objet `config` avec les sections : `version`, `project`,
  `ingestion`, `embedding`, `vector_store`, `retrieval`, `llm`, `agents`
- `config.project.name` correspond au nom defini dans ragkit.yaml

### 7.2 GET /api/v1/admin/config/defaults

```bash
curl -s http://localhost:8000/api/v1/admin/config/defaults
```

**PASS** :
- HTTP 200
- Le body contient les valeurs par defaut pour chaque section
- Les sections `ingestion`, `embedding`, `llm`, `agents` sont presentes

### 7.3 GET /api/v1/admin/config/export

```bash
curl -s http://localhost:8000/api/v1/admin/config/export
```

**PASS** :
- HTTP 200
- Le body est du YAML valide (commence par `version:`)
- Le contenu correspond a la configuration active

### 7.4 POST /api/v1/admin/config/validate - config valide

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/config/validate \
  -H "Content-Type: application/json" \
  -d '{"config": {"version": "1.0", "project": {"name": "test", "description": "test"}}}'
```

**PASS** :
- HTTP 200
- `{"valid": true, "errors": [], "warnings": []}`

### 7.5 POST /api/v1/admin/config/validate - config invalide

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/config/validate \
  -H "Content-Type: application/json" \
  -d '{"config": {"version": "1.0"}}'
```

**PASS** :
- HTTP 200 ou 422
- `valid` = `false` ou le body contient des erreurs de validation

---

## Phase 8 - Ingestion via API

### 8.1 GET /api/v1/admin/ingestion/status (etat initial)

```bash
curl -s http://localhost:8000/api/v1/admin/ingestion/status
```

**PASS** :
- HTTP 200
- `is_running` = `false`

### 8.2 POST /api/v1/admin/ingestion/run

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/ingestion/run \
  -H "Content-Type: application/json" \
  -d '{}'
```

**PASS** :
- HTTP 200
- Le body contient `job_id`, `status: "started"`, `message`
- **Sauvegarder** la valeur de `job_id` pour les etapes suivantes

### 8.3 Attendre la fin de l'ingestion

Attendre 30-60 secondes (selon la taille du corpus), puis :

```bash
curl -s http://localhost:8000/api/v1/admin/ingestion/status
```

**PASS** :
- `is_running` = `false`
- `last_run` est une date recente
- `last_stats.documents_loaded` > 0
- `last_stats.chunks_stored` > 0
- `last_stats.errors` = 0
- `total_documents` > 0
- `total_chunks` > 0

### 8.4 GET /api/v1/admin/ingestion/jobs/{job_id}

```bash
curl -s http://localhost:8000/api/v1/admin/ingestion/jobs/JOB_ID_ICI
```

**PASS** :
- HTTP 200
- `status` = `"completed"`
- `stats` contient les memes valeurs que l'ingestion CLI (Phase 3.2)

### 8.5 GET /api/v1/admin/ingestion/history

```bash
curl -s http://localhost:8000/api/v1/admin/ingestion/history
```

**PASS** :
- HTTP 200
- Le body est un tableau avec au moins 1 element
- Chaque element contient `id`, `started_at`, `completed_at`, `stats`, `status`
- `status` = `"completed"`

---

## Phase 9 - Query endpoint (coeur du RAG)

### 9.1 POST /api/v1/query - question simple

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "De quoi parlent les documents?", "history": []}'
```

**PASS** :
- HTTP 200
- Le body contient `answer`, `sources`, `metadata`
- `answer` est une reponse non vide faisant reference au contenu des documents
- `sources` est un tableau non vide (au moins 1 source)
- `metadata` contient un champ `intent`

### 9.2 POST /api/v1/query - avec sources citees

Verifier que la reponse cite les sources :

**PASS** : Le champ `answer` contient au moins une occurrence de `[Source:`.

### 9.3 POST /api/v1/query - salutation (pas de retrieval)

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Bonjour!", "history": []}'
```

**PASS** :
- HTTP 200
- `sources` est un tableau vide `[]`
- `metadata.intent` contient `"greeting"`
- `answer` est une reponse amicale courte

### 9.4 POST /api/v1/query - question hors scope

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quelle est la recette du tiramisu?", "history": []}'
```

**PASS** :
- HTTP 200
- La reponse ne fabrique pas de faux contenu a partir des documents
- Idealement, `metadata.intent` = `"out_of_scope"` (selon le comportement du LLM)

### 9.5 POST /api/v1/query - historique de conversation

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Peux-tu me donner plus de details?",
    "history": [
      {"role": "user", "content": "De quoi parle le premier document?"},
      {"role": "assistant", "content": "Le premier document parle de..."}
    ]
  }'
```

**PASS** :
- HTTP 200
- La reponse prend en compte le contexte de conversation
- Le retrieval utilise l'historique pour comprendre "plus de details" sur le sujet precedent

### 9.6 POST /api/v1/query - query vide

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "", "history": []}'
```

**PASS** :
- HTTP 422
- Le body contient une erreur de validation : `String should have at least 1 character`

### 9.7 POST /api/v1/query - body invalide

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{}'
```

**PASS** :
- HTTP 422
- Le body contient une erreur de validation (champ `query` requis)

### 9.8 POST /api/v1/query - sans Content-Type

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -d '{"query": "test"}'
```

**PASS** :
- HTTP 422 (le serveur rejette le body non JSON)

---

## Phase 10 - Endpoint streaming

### 10.1 POST /api/v1/query/stream - streaming desactive

(Avec la config par defaut ou `streaming.enabled: false`)

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Resumer les documents", "history": []}'
```

**PASS** :
- HTTP **501** (Not Implemented)
- Le message indique que le streaming est desactive

### 10.2 POST /api/v1/query/stream - streaming active

Modifier `ragkit.yaml` pour activer le streaming :

```yaml
api:
  streaming:
    enabled: true
    type: "sse"
```

Relancer le serveur, puis :

```bash
curl -s -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Resumer les documents", "history": []}'
```

**PASS** :
- Le serveur repond avec `Content-Type: text/event-stream`
- Le body contient des events SSE token par token :
  - `data: {"type":"delta","content":"..."}` (multiples lignes, une par token)
  - `data: {"type":"final","content":"...","sources":[...],"metadata":{...}}`
- Le contenu reconstitue est une reponse coherente
- Les sources et metadata sont presentes dans l'event `final`

---

## Phase 11 - Endpoints metriques

### 11.1 GET /api/v1/admin/metrics/summary

(Executer apres avoir fait plusieurs queries aux phases 9-10)

```bash
curl -s http://localhost:8000/api/v1/admin/metrics/summary
```

**PASS** :
- HTTP 200
- `queries.total` > 0
- `queries.success` > 0
- `queries.avg_latency_ms` > 0
- `components` contient `query_analyzer`, `retrieval`, `response_generator`
- Chaque composant a `calls` > 0 et `avg_latency_ms` > 0

### 11.2 GET /api/v1/admin/metrics/queries

```bash
curl -s http://localhost:8000/api/v1/admin/metrics/queries
```

**PASS** :
- HTTP 200
- Le body est un tableau non vide
- Chaque element contient : `query`, `intent`, `latency_ms`, `success`, `timestamp`
- Les queries correspondent a celles envoyees dans les phases precedentes

### 11.3 GET /api/v1/admin/metrics/timeseries/{metric}

```bash
curl -s http://localhost:8000/api/v1/admin/metrics/timeseries/query_latency
```

**PASS** :
- HTTP 200
- Le body est un tableau non vide (l'alias `query_latency` -> `query_latency_ms` est resolu)
- Chaque element contient `timestamp` et `value`

Verifier aussi le nom exact :

```bash
curl -s http://localhost:8000/api/v1/admin/metrics/timeseries/query_latency_ms
```

**PASS** : Memes resultats que ci-dessus.

---

## Phase 12 - Swagger / OpenAPI

### 12.1 GET /api/docs

```bash
curl -s http://localhost:8000/api/docs | head -c 100
```

**PASS** :
- HTTP 200
- Le body contient du HTML (page Swagger UI)
- Le contenu commence par `<!DOCTYPE html>` ou contient `swagger-ui`

### 12.2 GET /openapi.json

```bash
curl -s http://localhost:8000/openapi.json -o openapi.json
python -c "
import json
with open('openapi.json') as f:
    data = json.load(f)
paths = sorted(data['paths'].keys())
print(f'Endpoints: {len(paths)}')
for p in paths:
    methods = list(data['paths'][p].keys())
    for m in methods:
        print(f'  {m.upper():8s} {p}')
"
```

**PASS** :
- Le fichier est du JSON valide
- Le nombre d'endpoints est >= 17
- Les endpoints suivants sont presents :

```
GET      /api/status
GET      /api/v1/admin/config
PUT      /api/v1/admin/config
POST     /api/v1/admin/config/apply
GET      /api/v1/admin/config/defaults
GET      /api/v1/admin/config/export
POST     /api/v1/admin/config/validate
GET      /api/v1/admin/health/detailed
GET      /api/v1/admin/ingestion/history
GET      /api/v1/admin/ingestion/jobs/{job_id}
POST     /api/v1/admin/ingestion/run
GET      /api/v1/admin/ingestion/status
GET      /api/v1/admin/metrics/queries
GET      /api/v1/admin/metrics/summary
GET      /api/v1/admin/metrics/timeseries/{metric}
POST     /api/v1/query
POST     /api/v1/query/stream
GET      /health
```

---

## Phase 13 - Tests de robustesse

### 13.1 Ingestion pendant qu'une ingestion est deja en cours

Lancer une ingestion, puis immediatement une seconde :

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/ingestion/run -H "Content-Type: application/json" -d '{}'
sleep 1
curl -s -X POST http://localhost:8000/api/v1/admin/ingestion/run -H "Content-Type: application/json" -d '{}'
```

**PASS** :
- La seconde requete retourne une erreur ou un message indiquant qu'une ingestion
  est deja en cours
- OU la seconde requete est acceptee et mise en file d'attente
- Dans tous les cas, pas de crash serveur

### 13.2 Query pendant l'ingestion

Lancer une ingestion, puis envoyer une query :

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/ingestion/run -H "Content-Type: application/json" -d '{}'
sleep 2
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test pendant ingestion", "history": []}'
```

**PASS** :
- La query retourne une reponse (HTTP 200) ou une erreur propre (HTTP 503)
- Pas de crash serveur

### 13.3 Query avec un body tres long

```bash
LONG_QUERY=$(python -c "print('mot ' * 500)")
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$LONG_QUERY\", \"history\": []}"
```

**PASS** :
- Le serveur repond (HTTP 200 ou 422) sans crash
- Pas d'erreur 500

### 13.4 Query avec caracteres speciaux

```bash
curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test avec accents: eee, guillemets \"double\" et apostrophes l'\''exemple", "history": []}'
```

**PASS** :
- HTTP 200 avec une reponse
- Pas d'erreur d'encodage

---

## Phase 14 - Setup mode

### 14.1 Demarrer en mode setup

Creer un `setup.yaml` minimal sans sections LLM/embedding/agents :

```yaml
version: "1.0"
project:
  name: "setup-test"
  description: "Test setup mode"
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
    port: 8001
  cors:
    enabled: true
    origins: ["*"]
  docs:
    enabled: true
    path: "/docs"
```

Arreter le serveur precedent puis :

```bash
ragkit serve --config setup.yaml --api-only --no-ui &
sleep 5
```

### 14.2 Verifier le mode setup

```bash
curl -s http://localhost:8001/api/status
```

**PASS** :
- `setup_mode` = `true`
- `configured` = `false`

### 14.3 Query bloquee en mode setup

```bash
curl -s -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "history": []}'
```

**PASS** :
- HTTP 503
- Le message indique que le serveur est en mode setup

### 14.4 Les endpoints admin restent accessibles

```bash
curl -s http://localhost:8001/api/v1/admin/config
```

**PASS** :
- HTTP 200
- La configuration actuelle est retournee

Arreter le serveur :

```bash
kill %1 2>/dev/null
```

---

## Phase 15 - Test avec Qdrant (optionnel)

Repeter les phases 3, 5, 8, 9 avec la configuration vector_store suivante :

```yaml
vector_store:
  provider: "qdrant"
  qdrant:
    mode: "memory"
    collection_name: "ragkit_test"
    distance_metric: "cosine"
```

**PASS** : Memes resultats que Chroma pour l'ingestion et les queries.

---

## Phase 16 - Nettoyage

Depuis `C:\Users\henri\Projets\test_ragkit` :

```bash
kill %1 2>/dev/null  # arreter les serveurs en arriere-plan
rm -rf data/chroma data/qdrant .ragkit openapi.json mon-projet autre-projet
```

---

## Grille de synthese

Cocher chaque test apres execution :

| # | Phase | Test | Resultat |
|---|-------|------|----------|
| 0.3 | Installation | `ragkit --help` | [ ] |
| 1.1 | Init | Creer un projet | [ ] |
| 1.2 | Init | Nom deja existant | [ ] |
| 1.3 | Init | Template inconnu | [ ] |
| 2.2 | Config | Valider config OK | [ ] |
| 2.3 | Config | Cle API manquante | [ ] |
| 2.4 | Config | YAML invalide | [ ] |
| 3.2 | Ingestion CLI | Ingestion complete | [ ] |
| 3.3 | Ingestion CLI | Ingestion incrementale | [ ] |
| 3.4 | Ingestion CLI | Dossier vide | [ ] |
| 4.1 | Query CLI | Question simple | [ ] |
| 4.2 | Query CLI | Salutation | [ ] |
| 5.2 | Serveur | Health check | [ ] |
| 6.1 | Health | GET /health | [ ] |
| 6.2 | Status | GET /api/status | [ ] |
| 6.3 | Health | GET /admin/health/detailed | [ ] |
| 7.1 | Config | GET /admin/config | [ ] |
| 7.2 | Config | GET /admin/config/defaults | [ ] |
| 7.3 | Config | GET /admin/config/export | [ ] |
| 7.4 | Config | POST validate (valide) | [ ] |
| 7.5 | Config | POST validate (invalide) | [ ] |
| 8.1 | Ingestion API | Status initial | [ ] |
| 8.2 | Ingestion API | Lancer ingestion | [ ] |
| 8.3 | Ingestion API | Status apres ingestion | [ ] |
| 8.4 | Ingestion API | Job par ID | [ ] |
| 8.5 | Ingestion API | Historique | [ ] |
| 9.1 | Query | Question simple | [ ] |
| 9.2 | Query | Sources citees | [ ] |
| 9.3 | Query | Salutation | [ ] |
| 9.4 | Query | Hors scope | [ ] |
| 9.5 | Query | Historique conversation | [ ] |
| 9.6 | Query | Query vide | [ ] |
| 9.7 | Query | Body invalide | [ ] |
| 9.8 | Query | Sans Content-Type | [ ] |
| 10.1 | Streaming | Streaming desactive | [ ] |
| 10.2 | Streaming | Streaming active | [ ] |
| 11.1 | Metriques | Summary | [ ] |
| 11.2 | Metriques | Queries log | [ ] |
| 11.3 | Metriques | Timeseries | [ ] |
| 12.1 | Docs | Swagger UI | [ ] |
| 12.2 | Docs | OpenAPI JSON | [ ] |
| 13.1 | Robustesse | Double ingestion | [ ] |
| 13.2 | Robustesse | Query pendant ingestion | [ ] |
| 13.3 | Robustesse | Query tres longue | [ ] |
| 13.4 | Robustesse | Caracteres speciaux | [ ] |
| 14.1 | Setup | Demarrer en mode setup | [ ] |
| 14.2 | Setup | Verifier setup_mode | [ ] |
| 14.3 | Setup | Query bloquee | [ ] |
| 14.4 | Setup | Admin accessible | [ ] |

**Total : 45 tests**

Score minimum pour publication : **41/45** (toutes les phases sauf 10.2, 13.x, 15
qui sont optionnelles ou tolerantes).
