# RAGKIT

RAGKIT is a configuration-first agentic RAG framework. It lets you run an end-to-end RAG system with YAML config only.

## Features

- YAML-first configuration
- Modular ingestion, retrieval, and agents
- Multiple providers (LLM, embeddings, vector stores)
- Built-in API and chatbot UI
- Web UI dashboard + setup wizard
- Optional response streaming (API SSE and chatbot)

## Requirements

- Python 3.10+
- Node.js 18+ (only for `ragkit ui build` / `ragkit ui dev` or auto-build from source)

## Install (published)

```bash
pip install ragkit
```

## Install (dev / from repo)

```bash
git clone https://github.com/henribesnard/ragkit.git
cd ragkit
pip install -e ".[dev]"
```

## Quickstart (published setup flow)

```bash
ragkit init my-project
cd my-project
ragkit serve
```

Then open the setup UI at `http://localhost:8000` (or use `--port XXXX`) and complete the wizard.
The server starts in **setup mode** (no API keys required) until you apply a full config.

## Quickstart (manual config)

```bash
ragkit init my-project --template minimal
cd my-project
ragkit validate
ragkit ingest
ragkit query "What is this project about?"
```

Start the API (manual config):

```bash
ragkit serve --api-only
```

Start the chatbot (manual config):

```bash
ragkit serve --chatbot-only
```

Start both (manual config):

```bash
ragkit serve
```

If the Web UI assets are missing (source install), build them:

```bash
ragkit ui build
```

UI dev server (hot reload):

```bash
ragkit ui dev
```

## Configuration

Main config file: `ragkit.yaml` (see `templates/`).

Streaming flags:

- `chatbot.features.streaming`: enable or disable streaming in the chatbot UI
- `api.streaming.enabled`: enable or disable SSE streaming in the API

Notes:

- Manual config requires API keys for hosted providers (OpenAI/Cohere/Anthropic/DeepSeek/Groq/Mistral) or you can use local providers like Ollama.

## API

- `POST /api/v1/query` for normal responses
- `POST /api/v1/query/stream` for SSE streaming (when enabled)
- `GET /health`
- Admin endpoints under `/api/v1/admin/*` (config, ingestion, metrics, health)

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t ragkit .
docker run -p 8000:8000 -p 8080:8080 -v $(pwd)/ragkit.yaml:/app/ragkit.yaml ragkit
```

Or with docker-compose:

```bash
docker-compose up --build
```

## Project Plan

See `IMPLEMENTATION_PLAN.md` for the full roadmap.
