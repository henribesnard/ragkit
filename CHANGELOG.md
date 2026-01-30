# Changelog

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
