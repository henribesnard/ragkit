# Configuration

All configuration is YAML. The reference config is `ragkit-v1-config.yaml`.

## Top level

- `version`
- `project`
- `ingestion`
- `embedding`
- `vector_store`
- `retrieval`
- `llm`
- `agents`
- `conversation`
- `chatbot`
- `api`
- `observability`

## Ingestion

```yaml
ingestion:
  sources:
    - type: "local"
      path: "./data/documents"
      patterns: ["*.md", "*.txt"]
      recursive: true
  parsing:
    engine: "auto"
    ocr:
      enabled: false
  chunking:
    strategy: "fixed"
    fixed:
      chunk_size: 512
      chunk_overlap: 50
```

## Embedding

```yaml
embedding:
  document_model:
    provider: "openai"
    model: "text-embedding-3-small"
    api_key_env: "OPENAI_API_KEY"
  query_model:
    provider: "openai"
    model: "text-embedding-3-small"
    api_key_env: "OPENAI_API_KEY"
```

## Vector store

```yaml
vector_store:
  provider: "qdrant"  # qdrant | chroma
```

## Retrieval

```yaml
retrieval:
  architecture: "hybrid"
  semantic:
    enabled: true
    top_k: 20
  lexical:
    enabled: true
    top_k: 20
  rerank:
    enabled: false
```

## Agents

```yaml
agents:
  query_analyzer:
    llm: "fast"
  response_generator:
    llm: "primary"
```

## Chatbot

```yaml
chatbot:
  enabled: true
  features:
    show_sources: true
    show_latency: true
    streaming: false
```

## API

```yaml
api:
  enabled: true
  streaming:
    enabled: false
    type: "sse"
```
