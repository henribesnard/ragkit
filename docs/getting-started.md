# Getting Started

This guide shows the minimal setup to run RAGKIT.

## 1. Install

```bash
pip install -e ".[dev]"
```

## 2. Initialize a project

```bash
ragkit init my-project --template minimal
cd my-project
```

## 3. Validate config

```bash
ragkit validate
```

## 4. Add documents

Put files in `data/documents` (md, txt, pdf, docx, doc).
For legacy `.doc` files, install `antiword` or LibreOffice (`soffice`) for better extraction.

## 5. Ingest

```bash
ragkit ingest
```

Tip: `.env` files are auto-loaded (priority to the `.env` next to your `ragkit.yaml`).

## 6. Query

```bash
ragkit query "What is in the docs?"
```

## 7. Serve

API only:

```bash
ragkit serve --api-only
```

Chatbot only:

```bash
ragkit serve --chatbot-only
```

Both:

```bash
ragkit serve
```

## Streaming

Enable streaming in `ragkit.yaml`:

```yaml
chatbot:
  features:
    streaming: true

api:
  streaming:
    enabled: true
    type: "sse"
```

API streaming endpoint:

```
POST /api/v1/query/stream
```
