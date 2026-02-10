"""Parent-child chunking for enhanced context.

Parent-child chunking solves the granularity/context trade-off:
- CHILDREN are small (400 tokens) => precise retrieval
- PARENTS are large (2000 tokens) => context for the LLM

Workflow:
1. Create PARENT chunks of 2000 tokens with overlap
2. For each parent, create CHILDREN chunks of 400 tokens
3. Index ONLY children (embedding + VectorDB)
4. Store parent as metadata of each child
5. At retrieval: retrieve child + send parent to LLM for extended context
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from ragkit.config.schema_v2 import ChunkingConfigV2
from ragkit.ingestion.chunkers.base import BaseChunker
from ragkit.ingestion.chunkers.fixed import FixedChunker
from ragkit.ingestion.parsers.base import ParsedDocument
from ragkit.models import Chunk


def _document_id(document: ParsedDocument) -> str:
    """Extract document ID from metadata."""
    raw_id = document.metadata.get("document_id") or document.metadata.get("source_path")
    if raw_id:
        return Path(str(raw_id)).stem
    return "document"


class ParentChildChunker(BaseChunker):
    """Chunker creating parent-child hierarchy for enhanced context.

    Creates a parent-child hierarchy:
    - Parents: large chunks (2000 tokens) for context
    - Children: small chunks (400 tokens) for retrieval

    Example:
        Document of 5000 tokens:
        - Parent 1 (0-2000) -> 5 children of 400 tokens each
        - Parent 2 (1900-3900, overlap 100) -> 5 children
        - Parent 3 (3800-5000) -> 3 children

        Total: 13 children indexed, each with parent in metadata
    """

    def __init__(self, config: ChunkingConfigV2 | None = None, **kwargs):
        """Initialize the chunker.

        Args:
            config: Chunking configuration with parent_chunk_size and child_chunk_size
            **kwargs: Optional override for parent_chunk_size, child_chunk_size, overlap
        """
        self.config = config or ChunkingConfigV2()

        # Allow kwargs override
        parent_size = kwargs.get("parent_chunk_size", self.config.parent_chunk_size)
        child_size = kwargs.get("child_chunk_size", self.config.child_chunk_size)
        overlap = kwargs.get("parent_child_overlap", self.config.parent_child_overlap)

        # Chunker for creating parents
        self.parent_chunker = FixedChunker(chunk_size=parent_size, chunk_overlap=overlap)

        # Chunker for creating children
        self.child_chunker = FixedChunker(chunk_size=child_size, chunk_overlap=overlap)

    def chunk(self, document: ParsedDocument) -> list[Chunk]:
        """Create parent-child chunks (sync).

        Args:
            document: Parsed document to chunk

        Returns:
            List of CHILD chunks with metadata (parent_id, parent_content)

        Note:
            Only children are returned (for indexing).
            Parents are stored as metadata.
        """
        # Step 1: Create parent chunks
        parent_chunks = self.parent_chunker.chunk(document)

        if not parent_chunks:
            return []

        all_children = []
        doc_id = _document_id(document)

        # Step 2: For each parent, create children
        for parent_idx, parent in enumerate(parent_chunks):
            parent_id = self._generate_parent_id(parent, parent_idx, doc_id)

            # Create temporary document from parent
            parent_doc = ParsedDocument(content=parent.content, metadata=parent.metadata.copy())

            # Split parent into children
            child_chunks = self.child_chunker.chunk(parent_doc)

            # Step 3: Enrich each child with parent metadata
            for child_idx, child in enumerate(child_chunks):
                child_id = f"{parent_id}_child_{child_idx}"

                parent_content = parent.content
                if len(parent_content) <= len(child.content):
                    parent_content = document.content

                # Update child metadata
                child.id = child_id
                child.document_id = doc_id
                child.metadata.update(
                    {
                        "chunk_id": child_id,
                        "parent_id": parent_id,
                        "parent_content": parent_content,  # EXTENDED CONTEXT
                        "chunk_type": "child",
                        "child_index_in_parent": child_idx,
                        "total_children_in_parent": len(child_chunks),
                    }
                )

                # Copy document metadata if configured
                if self.config.add_document_title and "title" in document.metadata:
                    child.metadata["document_title"] = document.metadata["title"]

                if self.config.add_chunk_index:
                    # Global index in document
                    child.metadata["chunk_index"] = len(all_children)

                all_children.append(child)

        return all_children

    async def chunk_async(self, document: ParsedDocument) -> list[Chunk]:
        """Create parent-child chunks (async).

        Args:
            document: Parsed document to chunk

        Returns:
            List of CHILD chunks with metadata
        """
        # For now, use sync implementation
        # Can be optimized later with true async processing
        return self.chunk(document)

    def _generate_parent_id(self, parent: Chunk, parent_idx: int, doc_id: str) -> str:
        """Generate unique ID for a parent.

        Args:
            parent: Parent chunk
            parent_idx: Index of parent in document
            doc_id: Document ID

        Returns:
            Unique ID (hash MD5 of first 100 chars + index)
        """
        # Hash content for uniqueness
        content_hash = hashlib.md5(parent.content[:100].encode("utf-8")).hexdigest()[:8]

        return f"{doc_id}_parent_{parent_idx}_{content_hash}"
