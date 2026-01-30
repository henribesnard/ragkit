# Changelog

## [Unreleased]

### Added
- Web UI (React + Vite) with dashboard, setup wizard, chatbot test bench, and config editor
- Admin API endpoints for config, ingestion, metrics, and detailed health
- WebSocket endpoint for real-time events (`/api/v1/admin/ws`)
- Metrics and state modules with SQLite persistence
- CLI commands `ragkit ui build` and `ragkit ui dev`
- Vector store stats helpers (count/stats/list_documents)
- CLI integration tests

### Changed
- FastAPI now serves the built UI when `ragkit/ui/dist` exists and `ragkit serve --with-ui` is used

### Fixed
- Qdrant compatibility: use `query_points` when `search` is unavailable
- Gradio warning by moving `theme/title` to `launch()` parameters

## [1.0.0] - 2026-01-30

### Added
- YAML-first configuration system with validation and env resolution
- Ingestion pipeline (sources, parsers, chunkers) with incremental mode
- Embedding providers (OpenAI/Ollama/Cohere) and caching
- Vector stores (Qdrant/Chroma) with factories
- Retrieval engine (semantic, lexical, fusion, rerank)
- LLM wrapper (LiteLLM) and agents (query analyzer, response generator)
- API endpoints and Gradio chatbot UI
- Optional streaming (API SSE + chatbot streaming)
- CLI commands (init, validate, ingest, query, serve)
- E2E tests, docs, Docker, and CI workflow

### Notes
- API streaming is available at `/api/v1/query/stream` when enabled.
- Chatbot streaming is controlled via `chatbot.features.streaming`.
