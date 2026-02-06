"""Knowledge Base Manager for RAGKIT Desktop.

Provides a high-level interface for managing knowledge bases,
including their associated vector stores and documents.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ragkit.storage.sqlite_store import SQLiteStore
    from ragkit.vectorstore.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)

# Default vector store base path
DEFAULT_VECTORS_PATH = Path.home() / ".ragkit" / "vectors"


@dataclass
class KnowledgeBase:
    """Knowledge base data model."""

    id: str
    name: str
    description: str | None
    embedding_model: str
    embedding_dimensions: int
    vector_store_path: str | None
    document_count: int
    chunk_count: int
    created_at: str
    updated_at: str
    config: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeBase:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            embedding_model=data["embedding_model"],
            embedding_dimensions=data["embedding_dimensions"],
            vector_store_path=data.get("vector_store_path"),
            document_count=data.get("document_count", 0),
            chunk_count=data.get("chunk_count", 0),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            config=data.get("config", {}),
        )


@dataclass
class Document:
    """Document data model."""

    id: str
    kb_id: str
    source_path: str
    filename: str
    file_type: str | None
    file_size: int | None
    chunk_count: int
    hash: str | None
    status: str
    error_message: str | None
    created_at: str
    updated_at: str
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Document:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            kb_id=data["kb_id"],
            source_path=data["source_path"],
            filename=data["filename"],
            file_type=data.get("file_type"),
            file_size=data.get("file_size"),
            chunk_count=data.get("chunk_count", 0),
            hash=data.get("hash"),
            status=data.get("status", "pending"),
            error_message=data.get("error_message"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            metadata=data.get("metadata", {}),
        )


class KnowledgeBaseManager:
    """High-level manager for knowledge bases.

    Coordinates between SQLite metadata storage and ChromaDB vector storage.
    """

    def __init__(
        self,
        db: SQLiteStore,
        vectors_path: Path | None = None,
    ) -> None:
        """Initialize knowledge base manager.

        Args:
            db: SQLite store instance
            vectors_path: Base path for vector store directories
        """
        self.db = db
        self.vectors_path = vectors_path or DEFAULT_VECTORS_PATH
        self.vectors_path.mkdir(parents=True, exist_ok=True)
        self._vector_stores: dict[str, ChromaVectorStore] = {}

    async def create(
        self,
        name: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dimensions: int = 384,
        description: str | None = None,
        config: dict | None = None,
    ) -> KnowledgeBase:
        """Create a new knowledge base.

        Args:
            name: Unique name for the knowledge base
            embedding_model: Embedding model to use
            embedding_dimensions: Vector dimensions
            description: Optional description
            config: Additional configuration

        Returns:
            Created knowledge base.

        Raises:
            ValueError: If name already exists.
        """
        # Check for duplicate name
        existing = self.db.get_knowledge_base_by_name(name)
        if existing:
            raise ValueError(f"Knowledge base with name '{name}' already exists")

        # Create vector store directory
        kb_data = self.db.create_knowledge_base(
            name=name,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            description=description,
            config=config,
        )

        kb = KnowledgeBase.from_dict(kb_data)

        # Set up vector store path
        vector_store_path = self.vectors_path / kb.id
        vector_store_path.mkdir(parents=True, exist_ok=True)

        self.db.update_knowledge_base(
            kb.id,
            vector_store_path=str(vector_store_path),
        )
        kb.vector_store_path = str(vector_store_path)

        logger.info(f"Created knowledge base: {name} (id={kb.id})")
        return kb

    async def get(self, kb_id: str) -> KnowledgeBase | None:
        """Get a knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Knowledge base or None if not found.
        """
        data = self.db.get_knowledge_base(kb_id)
        return KnowledgeBase.from_dict(data) if data else None

    async def get_by_name(self, name: str) -> KnowledgeBase | None:
        """Get a knowledge base by name.

        Args:
            name: Knowledge base name

        Returns:
            Knowledge base or None if not found.
        """
        data = self.db.get_knowledge_base_by_name(name)
        return KnowledgeBase.from_dict(data) if data else None

    async def list(self) -> list[KnowledgeBase]:
        """List all knowledge bases.

        Returns:
            List of knowledge bases, most recently updated first.
        """
        items = self.db.list_knowledge_bases()
        return [KnowledgeBase.from_dict(item) for item in items]

    async def update(
        self,
        kb_id: str,
        name: str | None = None,
        description: str | None = None,
        config: dict | None = None,
    ) -> KnowledgeBase | None:
        """Update a knowledge base.

        Args:
            kb_id: Knowledge base ID
            name: New name (optional)
            description: New description (optional)
            config: New config (optional)

        Returns:
            Updated knowledge base or None if not found.
        """
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if config is not None:
            updates["config"] = config

        if not updates:
            return await self.get(kb_id)

        data = self.db.update_knowledge_base(kb_id, **updates)
        return KnowledgeBase.from_dict(data) if data else None

    async def delete(self, kb_id: str) -> bool:
        """Delete a knowledge base and all associated data.

        This removes:
        - SQLite metadata
        - Vector store directory
        - All documents

        Args:
            kb_id: Knowledge base ID

        Returns:
            True if deleted, False if not found.
        """
        kb = await self.get(kb_id)
        if not kb:
            return False

        # Remove vector store from cache
        if kb_id in self._vector_stores:
            del self._vector_stores[kb_id]

        # Delete vector store directory
        if kb.vector_store_path:
            vector_path = Path(kb.vector_store_path)
            if vector_path.exists():
                shutil.rmtree(vector_path)
                logger.info(f"Deleted vector store at {vector_path}")

        # Delete from SQLite (cascades to documents)
        deleted = self.db.delete_knowledge_base(kb_id)

        if deleted:
            logger.info(f"Deleted knowledge base: {kb.name} (id={kb_id})")

        return deleted

    async def update_stats(self, kb_id: str) -> None:
        """Update document and chunk counts for a knowledge base.

        Args:
            kb_id: Knowledge base ID
        """
        documents = self.db.list_documents(kb_id)
        document_count = len(documents)
        chunk_count = sum(doc.get("chunk_count", 0) for doc in documents)

        self.db.update_knowledge_base(
            kb_id,
            document_count=document_count,
            chunk_count=chunk_count,
        )

    def get_vector_store(self, kb_id: str) -> ChromaVectorStore:
        """Get or create a ChromaDB vector store for a knowledge base.

        Args:
            kb_id: Knowledge base ID

        Returns:
            ChromaDB vector store instance.

        Raises:
            ValueError: If knowledge base not found.
        """
        if kb_id in self._vector_stores:
            return self._vector_stores[kb_id]

        kb_data = self.db.get_knowledge_base(kb_id)
        if not kb_data:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        from ragkit.config.schema import ChromaConfig
        from ragkit.vectorstore.chroma import ChromaVectorStore

        vector_path = kb_data.get("vector_store_path")
        if not vector_path:
            vector_path = str(self.vectors_path / kb_id)

        config = ChromaConfig(
            mode="persistent",
            path=vector_path,
            collection_name=f"kb_{kb_id}",
        )

        store = ChromaVectorStore(
            config=config,
            embedding_dimensions=kb_data["embedding_dimensions"],
        )

        self._vector_stores[kb_id] = store
        return store

    # --- Document Operations ---

    async def add_document(
        self,
        kb_id: str,
        source_path: str,
        filename: str | None = None,
        metadata: dict | None = None,
    ) -> Document:
        """Add a document to a knowledge base.

        Args:
            kb_id: Knowledge base ID
            source_path: Path to source file
            filename: Optional filename override
            metadata: Optional metadata

        Returns:
            Created document record.

        Raises:
            ValueError: If knowledge base not found.
            FileNotFoundError: If source file doesn't exist.
        """
        # Validate KB exists
        kb = await self.get(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        # Validate file exists
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Get file info
        if filename is None:
            filename = path.name

        file_type = path.suffix.lstrip(".")
        file_size = path.stat().st_size

        # Create document record
        doc_data = self.db.create_document(
            kb_id=kb_id,
            source_path=str(path.absolute()),
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            metadata=metadata,
        )

        return Document.from_dict(doc_data)

    async def get_document(self, doc_id: str) -> Document | None:
        """Get a document by ID."""
        data = self.db.get_document(doc_id)
        return Document.from_dict(data) if data else None

    async def list_documents(
        self,
        kb_id: str,
        status: str | None = None,
    ) -> list[Document]:
        """List documents in a knowledge base.

        Args:
            kb_id: Knowledge base ID
            status: Optional status filter

        Returns:
            List of documents.
        """
        items = self.db.list_documents(kb_id, status)
        return [Document.from_dict(item) for item in items]

    async def update_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: str | None = None,
        chunk_count: int | None = None,
    ) -> Document | None:
        """Update document processing status.

        Args:
            doc_id: Document ID
            status: New status ('pending', 'processing', 'indexed', 'error')
            error_message: Error message if status is 'error'
            chunk_count: Number of chunks created

        Returns:
            Updated document or None if not found.
        """
        updates: dict = {"status": status}
        if error_message is not None:
            updates["error_message"] = error_message
        if chunk_count is not None:
            updates["chunk_count"] = chunk_count

        data = self.db.update_document(doc_id, **updates)
        return Document.from_dict(data) if data else None

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document.

        Note: This only removes the metadata. Vector store cleanup
        should be handled separately.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False if not found.
        """
        return self.db.delete_document(doc_id)
