# API Reference

Base URL: `http://localhost:8000`

## POST /api/v1/query

Request:

```json
{
  "query": "Your question",
  "history": []
}
```

Response:

```json
{
  "answer": "...",
  "sources": ["doc.pdf"],
  "metadata": {}
}
```

## POST /api/v1/query/stream

SSE streaming endpoint. Only available when `api.streaming.enabled` is true.

Each SSE event:

```json
{
  "content": "partial text",
  "done": false
}
```

Final event:

```json
{
  "content": "",
  "done": true
}
```

## GET /health

Response:

```json
{
  "status": "ok"
}
```
