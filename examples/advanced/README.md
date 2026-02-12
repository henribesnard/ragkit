# Advanced Example

This folder documents a richer setup (hybrid retrieval, rerank, and streaming).

Key config flags:

```yaml
retrieval:
  architecture: "hybrid_rerank"
  rerank:
    enabled: true

chatbot:
  features:
    streaming: true

api:
  streaming:
    enabled: true
```
