# Changelog

## [Unreleased]

### Added

#### Desktop Application (Tauri)
- Native cross-platform desktop app (Windows, macOS, Linux) using Tauri 2.0
- React + TypeScript frontend with Tailwind CSS
- Python FastAPI backend running as sidecar process
- Knowledge base management (create, delete, add documents)
- Conversation management with chat history
- Ollama integration for local models (status, model list, pull, delete)
- Secure API key storage with system keyring
- Settings management (theme, embedding/LLM providers)
- GitHub Actions CI/CD for multi-platform builds

#### Web UI
- Dashboard, setup wizard, chatbot test bench, and config editor
- Real SSE streaming in chatbot with progressive token display and fallback
- `match_query` and `match_documents` options for `response_language`
- `*.doc` pattern in setup wizard source configuration
- Enriched debug panel with detected/response language and streaming status

#### Backend
- Admin API endpoints for config, ingestion, metrics, and detailed health
- WebSocket endpoint for real-time events (`/api/v1/admin/ws`)
- Metrics and state modules with SQLite persistence
- Vector store stats helpers (count/stats/list_documents)
- Real token-by-token SSE streaming via `process_stream()` / `generate_stream()`
- Intent validation: `_clamp_intent()` clamps unknown intents to configured list
- Auto `.env` loading via `python-dotenv` in CLI and server
- Response language detection: `auto` and `match_query` modes via `langdetect`
- Metrics timeseries aliases (`query_latency` -> `query_latency_ms`, etc.)
- Configurable `add_batch_size` for ChromaDB and Qdrant vector stores
- Active LLM/embedding health checks with `api.health.active_checks` config
- Ingestion status sync on server startup for persistent vector stores
- Source path sanitization with `source_path_mode: basename`
- OCR language auto-detection from document samples
- Language utility module (`ragkit/utils/language.py`)
- CLI commands `ragkit ui build` and `ragkit ui dev`
- CLI integration tests

### Changed
- Templates (minimal, hybrid, full) updated with enriched query analyzer prompt
- FastAPI now serves the built UI when `ragkit/ui/dist` exists
- Streaming disabled endpoint returns HTTP 501 instead of 404
- UI chatbot falls back to non-streaming query on 501
- `.doc` files now route to `partition_doc` + `antiword` fallback

### Fixed
- Enriched query analyzer default prompt for reliable `out_of_scope` detection
- Enforce intent/needs_retrieval coherence in `_clamp_intent`
- Response generator checks `out_of_scope` intent before `needs_retrieval`
- Inject `uncertainty_phrase` into RAG system prompt when `admit_uncertainty` enabled
- Language detection uses `detect_langs` with confidence threshold and French bias
- Mask `api_key` values in `/admin/config` endpoints (security)
- Pydantic serializer warnings suppressed for all LLM providers
- Qdrant compatibility: use `query_points` when `search` unavailable
- ChromaDB batch size overflow: chunks inserted in batches (default 100)
- Metrics timeseries metric name mismatch

## [1.5.0] - 2026-02-06

### Added
- Desktop application foundation with Tauri 2.0
- Desktop backend API (`ragkit.desktop` module)
- Knowledge base manager with SQLite storage
- Conversation manager with message history
- Ollama service manager for local models
- Secure keyring integration for API keys
- Desktop CI/CD pipeline for Windows, macOS, and Linux

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
- API streaming available at `/api/v1/query/stream` when enabled
- Chatbot streaming controlled via `chatbot.features.streaming`
