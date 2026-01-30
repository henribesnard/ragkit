# RAGKIT

RAGKIT is a configuration-first agentic RAG framework. It lets you run an end-to-end RAG system with YAML config only.

## Features

- YAML-first configuration
- Modular ingestion, retrieval, and agents
- Multiple providers (LLM, embeddings, vector stores)
- Built-in API and chatbot UI
- Optional response streaming (API SSE and chatbot)

## Requirements

- Python 3.10+

## Install

```bash
pip install -e ".[dev]"
```

## Quickstart

```bash
ragkit init my-project --template minimal
cd my-project
ragkit validate
ragkit ingest
ragkit query "What is this project about?"
```

Start the API:

```bash
ragkit serve --api-only
```

Start the chatbot:

```bash
ragkit serve --chatbot-only
```

Start both:

```bash
ragkit serve
```

## Configuration

Main config file: `ragkit.yaml` (see `templates/`).

Streaming flags:

- `chatbot.features.streaming`: enable or disable streaming in the chatbot UI
- `api.streaming.enabled`: enable or disable SSE streaming in the API

## API

- `POST /api/v1/query` for normal responses
- `POST /api/v1/query/stream` for SSE streaming (when enabled)
- `GET /health`

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
