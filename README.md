# RAGKIT

[![Release](https://img.shields.io/github/v/release/henribesnard/ragkit)](https://github.com/henribesnard/ragkit/releases/latest)

RAGKIT is a configuration-first agentic RAG framework. It lets you run an end-to-end RAG system with YAML config only, available as a CLI tool, web server, or desktop application.

## Features

- **Configuration-First**: YAML-first configuration with `.env` auto-loading
- **Modular Architecture**: Ingestion, retrieval, and agents are fully configurable
- **Multiple LLM Providers**: OpenAI, Anthropic, DeepSeek, Groq, Mistral, Ollama
- **Multiple Embedding Providers**: OpenAI, Ollama, Cohere
- **Vector Stores**: ChromaDB and Qdrant with configurable batch sizes
- **Real-Time Streaming**: Token-by-token SSE streaming (API and chatbot UI)
- **Smart Detection**: Intent detection and automatic response language matching
- **Desktop Application**: Native cross-platform app (Windows, macOS, Linux) with Tauri

## Requirements

### CLI / Web Server

- Python 3.10+
- Node.js 18+ (for UI build)
- Optional: `antiword` or LibreOffice for legacy `.doc` files

### Desktop Application

- Python 3.10+
- Node.js 18+
- Rust 1.70+ (for Tauri)

## Installation

### Option 1: Install from PyPI (CLI/Web only)

```bash
pip install ragkit
```

### Option 2: Install from Source (Development)

```bash
git clone https://github.com/henribesnard/ragkit.git
cd ragkit
pip install -e ".[dev]"
```

### Option 3: Desktop Application

Prebuilt installers are available on GitHub Releases:
https://github.com/henribesnard/ragkit/releases/latest

1. **Install Prerequisites**

   - Python 3.10+
   - Node.js 18+
   - Rust: https://rustup.rs/

2. **Clone and Setup**

   ```bash
   git clone https://github.com/henribesnard/ragkit.git
   cd ragkit
   pip install -e ".[dev]"
   ```

3. **Install Frontend Dependencies**

   ```bash
   cd desktop
   npm install
   ```

4. **Run in Development Mode**

   ```bash
   npm run tauri dev
   ```

5. **Build for Production**

   ```bash
   npm run tauri build
   ```

   The built application will be in `desktop/src-tauri/target/release/`.

## Quick Start

### CLI Usage

```bash
# Initialize a new project
ragkit init my-project
cd my-project

# Start the server (opens setup wizard)
ragkit serve
```

Open `http://localhost:8000` and complete the setup wizard.

### Manual Configuration

```bash
ragkit init my-project --template minimal
cd my-project
ragkit validate
ragkit ingest
ragkit query "What is this project about?"
```

### Server Modes

```bash
# API only
ragkit serve --api-only

# Chatbot only
ragkit serve --chatbot-only

# Full server (API + chatbot + Web UI)
ragkit serve
```

### Desktop Application

Launch the desktop app and:

1. **Setup**: Configure your embedding and LLM providers
2. **Knowledge Bases**: Create and manage your document collections
3. **Chat**: Query your knowledge bases in a native interface

The desktop app supports:

- Local models via Ollama (no API keys required)
- Cloud providers (OpenAI, Anthropic, etc.) with API key management
- Secure local storage for credentials

## Configuration

### Configuration File

Main config file: `ragkit.yaml` (see `templates/` for examples).

### Environment Variables

- `.env` files are auto-loaded
- `*_env` fields in `ragkit.yaml` resolve from environment variables

### Streaming

```yaml
chatbot:
  features:
    streaming: true  # Enable streaming in chatbot UI

api:
  streaming:
    enabled: true  # Enable SSE streaming in API
```

### Providers

The following providers are supported:

| Provider  | LLM | Embedding | API Key Required |
|-----------|-----|-----------|------------------|
| OpenAI    | Yes | Yes       | Yes              |
| Anthropic | Yes | No        | Yes              |
| DeepSeek  | Yes | No        | Yes              |
| Groq      | Yes | No        | Yes              |
| Mistral   | Yes | No        | Yes              |
| Ollama    | Yes | Yes       | No (local)       |
| Cohere    | No  | Yes       | Yes              |

## API Reference

### Query Endpoints

- `POST /api/v1/query` - Standard query
- `POST /api/v1/query/stream` - SSE streaming query

### Health

- `GET /health` - Basic health check

### Admin Endpoints

- `GET /api/v1/admin/config` - Get configuration
- `POST /api/v1/admin/ingest` - Trigger ingestion
- `GET /api/v1/admin/metrics` - Get metrics
- `GET /api/v1/admin/health` - Detailed health status

## Development

### Run Tests

```bash
pytest
```

### Lint and Format

```bash
ruff check .
ruff format .
mypy ragkit
```

### Desktop Development

```bash
cd desktop

# Lint frontend
npm run lint

# Format frontend
npm run format

# Type check Rust
cd src-tauri && cargo check
```

## Docker

```bash
# Build
docker build -t ragkit .

# Run
docker run -p 8000:8000 -p 8080:8080 \
  -v $(pwd)/ragkit.yaml:/app/ragkit.yaml \
  ragkit
```

Or with docker-compose:

```bash
docker-compose up --build
```

## Project Structure

```
ragkit/
├── ragkit/              # Python package
│   ├── api/             # FastAPI server
│   ├── agents/          # LLM agents
│   ├── config/          # Configuration loading
│   ├── desktop/         # Desktop backend API
│   ├── embedding/       # Embedding providers
│   ├── ingestion/       # Document ingestion
│   ├── llm/             # LLM providers
│   ├── retrieval/       # Retrieval engine
│   ├── storage/         # Vector stores
│   └── ui/              # Web UI assets
├── desktop/             # Tauri desktop app
│   ├── src/             # React frontend
│   └── src-tauri/       # Rust backend
├── templates/           # YAML config templates
└── tests/               # Test suite
```

## License

MIT
