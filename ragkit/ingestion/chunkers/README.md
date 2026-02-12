# Chunking Strategies

This module implements multiple chunking strategies for RAG systems.

## Available Strategies

### 1. Fixed Size Chunking (`fixed_size`)
**Best for**: Baseline, prototyping, performance-critical applications

Simple chunking with fixed token size and overlap.

```python
from ragkit.ingestion.chunkers.factory import create_chunker

chunker = create_chunker("fixed_size", chunk_size=512, chunk_overlap=50)
chunks = await chunker.chunk_async(document)
```

**Pros**: Fast, predictable
**Cons**: Ignores semantic boundaries

---

### 2. Parent-Child Chunking (`parent_child`)
**Best for**: Technical documentation, API docs, manuals

Creates hierarchical parent-child structure for enhanced context.

```python
chunker = create_chunker(
    "parent_child",
    parent_chunk_size=2000,  # Large context for LLM
    child_chunk_size=400,    # Precise retrieval
    parent_child_overlap=100
)
chunks = await chunker.chunk_async(document)

# Each child chunk has parent context in metadata
for chunk in chunks:
    print(chunk.metadata["parent_content"])  # Full parent context
```

**Pros**: Best context preservation, high precision
**Cons**: 2x storage (parents stored in metadata)

---

### 3. Semantic Chunking (`semantic`)
**Best for**: Narrative documents, articles, books

Splits on topic changes using sentence similarity.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

chunker = create_chunker(
    "semantic",
    semantic_similarity_threshold=0.85,
    semantic_buffer_size=1,
    embedder=model
)
chunks = await chunker.chunk_async(document)
```

**Pros**: Respects semantic boundaries, coherent chunks
**Cons**: Slower (requires embeddings), more RAM

---

### 4. Sliding Window Chunking (`sliding_window`)
**Best for**: FAQ, Q&A, dialogues

Each sentence gets surrounding context.

```python
chunker = create_chunker(
    "sliding_window",
    sentence_window_size=3,  # 3 sentences before/after
    window_stride=1          # Move 1 sentence at a time
)
chunks = await chunker.chunk_async(document)
```

**Pros**: Good local context, works well for Q&A
**Cons**: Redundancy, more chunks

---

### 5. Recursive Chunking (`recursive`)
**Best for**: Markdown, code, structured documents

Respects document structure by trying hierarchical separators.

```python
chunker = create_chunker(
    "recursive",
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " "]  # Try in order
)
chunks = await chunker.chunk_async(document)
```

**Pros**: Preserves structure, natural boundaries
**Cons**: More complex

---

## Using ChunkerFactory

```python
from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.factory import ChunkerFactory

# Create configuration
config = ChunkingConfigV2(
    strategy="parent_child",
    parent_chunk_size=2000,
    child_chunk_size=400,
    add_document_title=True
)

# Create chunker from config
chunker = ChunkerFactory.create(config)

# Use it
chunks = await chunker.chunk_async(document)
```

## Performance Comparison

| Strategy | Speed | Quality | Storage | Best Use Case |
|----------|-------|---------|---------|---------------|
| Fixed Size | ⚡⚡⚡ | ⭐⭐ | ✅ | Prototyping |
| Semantic | ⚡ | ⭐⭐⭐⭐ | ✅ | Narrative docs |
| Parent-Child | ⚡⚡ | ⭐⭐⭐⭐⭐ | ❌ (2x) | Technical docs |
| Sliding Window | ⚡⚡⚡ | ⭐⭐⭐ | ⚠️ | FAQ/Q&A |
| Recursive | ⚡⚡ | ⭐⭐⭐ | ✅ | Markdown/Code |

## Strategy Selection Guide

**Choose Fixed Size if**:
- You need maximum speed
- You're prototyping
- Content type doesn't matter much

**Choose Semantic if**:
- You have narrative content (articles, books)
- Quality > speed
- You want chunks grouped by topic

**Choose Parent-Child if**:
- You have technical documentation
- You need both precision and context
- Storage is not a constraint

**Choose Sliding Window if**:
- You have Q&A or FAQ content
- Each sentence needs surrounding context
- Redundancy is acceptable

**Choose Recursive if**:
- You have structured content (Markdown, code)
- You want to respect document structure
- You have hierarchical content

## Examples

### Example 1: Technical Documentation Pipeline

```python
from ragkit.ingestion.chunkers.factory import create_chunker
from ragkit.ingestion.parsers.base import ParsedDocument

# Parse document
document = ParsedDocument(
    content="API documentation...",
    metadata={"title": "API Docs", "source": "api.md"}
)

# Use parent-child for technical docs
chunker = create_chunker(
    "parent_child",
    parent_chunk_size=2000,
    child_chunk_size=400
)

# Chunk it
chunks = await chunker.chunk_async(document)

# Children are indexed in VectorDB
for chunk in chunks:
    print(f"Child: {chunk.content[:50]}...")
    print(f"Parent context: {chunk.metadata['parent_content'][:50]}...")
```

### Example 2: FAQ System

```python
# Parse FAQ document
document = ParsedDocument(
    content="Q: How to install? A: Run pip install... Q: How to configure?...",
    metadata={"title": "FAQ"}
)

# Use sliding window for FAQ
chunker = create_chunker(
    "sliding_window",
    sentence_window_size=3,  # 3 sentences of context
    window_stride=1
)

chunks = await chunker.chunk_async(document)
```

### Example 3: Blog Articles

```python
# Parse blog article
document = ParsedDocument(
    content="Introduction to AI... Machine Learning... Deep Learning...",
    metadata={"title": "AI Guide"}
)

# Use semantic chunking for coherent topics
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

chunker = create_chunker(
    "semantic",
    semantic_similarity_threshold=0.85,
    embedder=model
)

chunks = await chunker.chunk_async(document)
```

## Testing

Run tests:
```bash
pytest tests/test_chunking_*.py -v
```

Run specific strategy tests:
```bash
pytest tests/test_chunking_parent_child.py -v
pytest tests/test_chunking_sliding_window.py -v
pytest tests/test_chunking_integration.py -v
```
