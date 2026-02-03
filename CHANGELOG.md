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
- Real token-by-token SSE streaming via `process_stream()` / `generate_stream()` (H1)
- Intent validation: `_clamp_intent()` clamps unknown intents to configured `detect_intents` list with coherent `needs_retrieval` (H2)
- Auto `.env` loading via `python-dotenv` in CLI and server (H3)
- Response language detection: `auto` and `match_query` modes detect query language via `langdetect` (M1)
- Metrics timeseries aliases (`query_latency` -> `query_latency_ms`, etc.) (M4)
- Configurable `add_batch_size` for ChromaDB and Qdrant vector stores (M5)
- Active LLM/embedding health checks with `api.health.active_checks` config (M3)
- Ingestion status sync on server startup for persistent vector stores (L1)
- LiteLLM/Pydantic warning filter for all providers (L2)
- Source path sanitization with `source_path_mode: basename` (L3)
- OCR language auto-detection from document samples (L4)
- Unit tests for `.doc` and `.docx` parsing (L5)
- Language utility module (`ragkit/utils/language.py`)
- Backend test procedure (`BACKEND_TEST_PROCEDURE.md`)
- UI: SSE streaming in chatbot with progressive token display and fallback (UI-1)
- UI: `match_query` and `match_documents` options for `response_language` (UI-2)
- UI: `*.doc` pattern in setup wizard source configuration (UI-3)
- UI: Enriched debug panel with detected/response language and streaming status (UI-5)

### Changed
- Templates (minimal, hybrid, full) updated with enriched query analyzer prompt and `*.doc` patterns
- FastAPI now serves the built UI when `ragkit/ui/dist` exists and `ragkit serve --with-ui` is used
- Streaming disabled endpoint returns HTTP 501 instead of 404 (M2)
- UI chatbot falls back to non-streaming query on 501 with user-friendly message (UI-4)
- `.doc` files now route to `partition_doc` + `antiword` fallback instead of `partition_docx` (H4)
- DOC parser warns when `antiword`/`soffice` are missing (H4)
- `_extract_with_antiword` now cleans up temp files in `finally` block (H4)

### Fixed
- Enriched query analyzer default prompt with explicit intent definitions for reliable `out_of_scope` detection
- Enforce intent/needs_retrieval coherence in `_clamp_intent` (e.g. `out_of_scope` forces `needs_retrieval=False`)
- Response generator checks `out_of_scope` intent before `needs_retrieval` to use the correct prompt
- Inject `uncertainty_phrase` into RAG system prompt when `admit_uncertainty` is enabled
- Language detection uses `detect_langs` with confidence threshold and French bias for short romance-language text
- Mask `api_key` values in `/admin/config` and `/admin/config/export` responses (security)
- Pydantic serializer warnings now suppressed for all LLM providers, not just DeepSeek
- Qdrant compatibility: use `query_points` when `search` is unavailable
- Gradio warning by moving `theme/title` to `launch()` parameters
- ChromaDB batch size overflow: chunks are now inserted in batches (default 100)
- Old `.doc` binary format was not parsed correctly (routed to wrong `unstructured` partition)
- Metrics timeseries returned empty due to metric name mismatch (`query_latency` vs `query_latency_ms`)

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
