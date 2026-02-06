"""SQLite storage backend for RAGKIT Desktop.

This module provides a SQLite-based storage layer for:
- Knowledge bases metadata
- Documents metadata
- Conversations and messages
- Application settings
- Encrypted API keys storage
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Schema version for migrations
SCHEMA_VERSION = 1

# Default database path
DEFAULT_DB_PATH = Path.home() / ".ragkit" / "ragkit.db"

# SQL schema definitions
SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Knowledge bases
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    embedding_model TEXT NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    vector_store_path TEXT,
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    config_json TEXT
);

-- Documents (source files indexed in knowledge bases)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    kb_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    chunk_count INTEGER DEFAULT 0,
    hash TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    kb_id TEXT,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL
);

-- Messages within conversations
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sources_json TEXT,
    latency_ms INTEGER,
    token_count INTEGER,
    created_at TEXT NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Application settings (key-value store)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Encrypted API keys
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL UNIQUE,
    encrypted_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_documents_kb_id ON documents(kb_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_conversations_kb_id ON conversations(kb_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
"""


class SQLiteStore:
    """SQLite-based storage for RAGKIT Desktop application data.

    Handles:
    - Connection management with thread safety
    - Schema creation and migrations
    - CRUD operations for all entity types
    - JSON serialization for complex fields
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Initialize SQLite store.

        Args:
            db_path: Path to database file. Defaults to ~/.ragkit/ragkit.db
        """
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)

            # Check and update schema version
            cursor = conn.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            )
            row = cursor.fetchone()

            if row is None:
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (SCHEMA_VERSION, _now()),
                )
            elif row[0] < SCHEMA_VERSION:
                self._migrate(conn, row[0], SCHEMA_VERSION)

            conn.commit()
        logger.info(f"SQLite store initialized at {self.db_path}")

    def _migrate(self, conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
        """Run database migrations.

        Args:
            conn: Database connection
            from_version: Current schema version
            to_version: Target schema version
        """
        logger.info(f"Migrating database from v{from_version} to v{to_version}")
        # Add migration logic here as schema evolves
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            (to_version, _now()),
        )

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection with automatic commit/rollback.

        Yields:
            SQLite connection with row factory enabled.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # --- Knowledge Base Operations ---

    def create_knowledge_base(
        self,
        name: str,
        embedding_model: str,
        embedding_dimensions: int,
        description: str | None = None,
        vector_store_path: str | None = None,
        config: dict | None = None,
    ) -> dict:
        """Create a new knowledge base.

        Args:
            name: Unique name for the knowledge base
            embedding_model: Embedding model identifier
            embedding_dimensions: Embedding vector dimensions
            description: Optional description
            vector_store_path: Path to vector store directory
            config: Additional configuration as dict

        Returns:
            Created knowledge base as dict.

        Raises:
            sqlite3.IntegrityError: If name already exists.
        """
        kb_id = str(uuid4())
        now = _now()

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_bases
                (id, name, description, embedding_model, embedding_dimensions,
                 vector_store_path, created_at, updated_at, config_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kb_id,
                    name,
                    description,
                    embedding_model,
                    embedding_dimensions,
                    vector_store_path,
                    now,
                    now,
                    json.dumps(config) if config else None,
                ),
            )

        return self.get_knowledge_base(kb_id)  # type: ignore

    def get_knowledge_base(self, kb_id: str) -> dict | None:
        """Get a knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            Knowledge base as dict, or None if not found.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,))
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    def get_knowledge_base_by_name(self, name: str) -> dict | None:
        """Get a knowledge base by name.

        Args:
            name: Knowledge base name

        Returns:
            Knowledge base as dict, or None if not found.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM knowledge_bases WHERE name = ?", (name,))
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    def list_knowledge_bases(self) -> list[dict]:
        """List all knowledge bases.

        Returns:
            List of knowledge bases as dicts.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM knowledge_bases ORDER BY updated_at DESC")
            return [d for row in cursor.fetchall() if (d := _row_to_dict(row)) is not None]

    def update_knowledge_base(self, kb_id: str, **kwargs: Any) -> dict | None:
        """Update a knowledge base.

        Args:
            kb_id: Knowledge base ID
            **kwargs: Fields to update

        Returns:
            Updated knowledge base, or None if not found.
        """
        allowed_fields = {
            "name",
            "description",
            "document_count",
            "chunk_count",
            "vector_store_path",
            "config",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return self.get_knowledge_base(kb_id)

        # Handle config -> config_json conversion
        if "config" in updates:
            updates["config_json"] = json.dumps(updates.pop("config"))

        updates["updated_at"] = _now()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [kb_id]

        with self.connection() as conn:
            conn.execute(
                f"UPDATE knowledge_bases SET {set_clause} WHERE id = ?",
                values,
            )

        return self.get_knowledge_base(kb_id)

    def delete_knowledge_base(self, kb_id: str) -> bool:
        """Delete a knowledge base and all related data.

        Args:
            kb_id: Knowledge base ID

        Returns:
            True if deleted, False if not found.
        """
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))
            return cursor.rowcount > 0

    # --- Document Operations ---

    def create_document(
        self,
        kb_id: str,
        source_path: str,
        filename: str,
        file_type: str | None = None,
        file_size: int | None = None,
        file_hash: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create a document record.

        Args:
            kb_id: Parent knowledge base ID
            source_path: Full path to source file
            filename: File name
            file_type: File extension/type
            file_size: File size in bytes
            file_hash: Content hash for change detection
            metadata: Additional metadata

        Returns:
            Created document as dict.
        """
        doc_id = str(uuid4())
        now = _now()

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO documents
                (id, kb_id, source_path, filename, file_type, file_size,
                 hash, status, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (
                    doc_id,
                    kb_id,
                    source_path,
                    filename,
                    file_type,
                    file_size,
                    file_hash,
                    now,
                    now,
                    json.dumps(metadata) if metadata else None,
                ),
            )

        return self.get_document(doc_id)  # type: ignore

    def get_document(self, doc_id: str) -> dict | None:
        """Get a document by ID."""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    def list_documents(self, kb_id: str, status: str | None = None) -> list[dict]:
        """List documents in a knowledge base.

        Args:
            kb_id: Knowledge base ID
            status: Optional status filter

        Returns:
            List of documents.
        """
        with self.connection() as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM documents WHERE kb_id = ? AND status = ? "
                    "ORDER BY created_at DESC",
                    (kb_id, status),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM documents WHERE kb_id = ? ORDER BY created_at DESC",
                    (kb_id,),
                )
            return [d for row in cursor.fetchall() if (d := _row_to_dict(row)) is not None]

    def update_document(self, doc_id: str, **kwargs: Any) -> dict | None:
        """Update a document record."""
        allowed_fields = {"status", "error_message", "chunk_count", "hash", "metadata"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return self.get_document(doc_id)

        if "metadata" in updates:
            updates["metadata_json"] = json.dumps(updates.pop("metadata"))

        updates["updated_at"] = _now()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [doc_id]

        with self.connection() as conn:
            conn.execute(
                f"UPDATE documents SET {set_clause} WHERE id = ?",
                values,
            )

        return self.get_document(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            return cursor.rowcount > 0

    # --- Conversation Operations ---

    def create_conversation(
        self,
        kb_id: str | None = None,
        title: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create a new conversation.

        Args:
            kb_id: Optional linked knowledge base
            title: Conversation title
            metadata: Additional metadata

        Returns:
            Created conversation as dict.
        """
        conv_id = str(uuid4())
        now = _now()

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations
                (id, kb_id, title, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_id,
                    kb_id,
                    title,
                    now,
                    now,
                    json.dumps(metadata) if metadata else None,
                ),
            )

        return self.get_conversation(conv_id)  # type: ignore

    def get_conversation(self, conv_id: str) -> dict | None:
        """Get a conversation by ID."""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    def list_conversations(
        self,
        kb_id: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """List conversations, optionally filtered by knowledge base.

        Args:
            kb_id: Optional knowledge base filter
            limit: Maximum number to return

        Returns:
            List of conversations, most recent first.
        """
        with self.connection() as conn:
            if kb_id:
                cursor = conn.execute(
                    """
                    SELECT * FROM conversations
                    WHERE kb_id = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (kb_id, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM conversations
                    ORDER BY updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            return [d for row in cursor.fetchall() if (d := _row_to_dict(row)) is not None]

    def update_conversation(self, conv_id: str, **kwargs: Any) -> dict | None:
        """Update a conversation."""
        allowed_fields = {"title", "kb_id", "metadata"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return self.get_conversation(conv_id)

        if "metadata" in updates:
            updates["metadata_json"] = json.dumps(updates.pop("metadata"))

        updates["updated_at"] = _now()

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [conv_id]

        with self.connection() as conn:
            conn.execute(
                f"UPDATE conversations SET {set_clause} WHERE id = ?",
                values,
            )

        return self.get_conversation(conv_id)

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation and all its messages."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            return cursor.rowcount > 0

    # --- Message Operations ---

    def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict] | None = None,
        latency_ms: int | None = None,
        token_count: int | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create a message in a conversation.

        Args:
            conversation_id: Parent conversation ID
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            sources: Source citations
            latency_ms: Response latency in milliseconds
            token_count: Token count
            metadata: Additional metadata

        Returns:
            Created message as dict.
        """
        msg_id = str(uuid4())
        now = _now()

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO messages
                (id, conversation_id, role, content, sources_json,
                 latency_ms, token_count, created_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id,
                    conversation_id,
                    role,
                    content,
                    json.dumps(sources) if sources else None,
                    latency_ms,
                    token_count,
                    now,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            # Update conversation's updated_at
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )

        return self.get_message(msg_id)  # type: ignore

    def get_message(self, msg_id: str) -> dict | None:
        """Get a message by ID."""
        with self.connection() as conn:
            cursor = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    def list_messages(self, conversation_id: str) -> list[dict]:
        """List all messages in a conversation, ordered by creation time.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages in chronological order.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )
            return [d for row in cursor.fetchall() if (d := _row_to_dict(row)) is not None]

    # --- Settings Operations ---

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT value_json FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return default

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value.

        Args:
            key: Setting key
            value: Value (must be JSON serializable)
        """
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (key, json.dumps(value), _now()),
            )

    def delete_setting(self, key: str) -> bool:
        """Delete a setting."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM settings WHERE key = ?", (key,))
            return cursor.rowcount > 0

    # --- API Key Operations ---

    def store_api_key(self, provider: str, encrypted_key: str) -> None:
        """Store an encrypted API key.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            encrypted_key: Encrypted key string
        """
        now = _now()
        key_id = str(uuid4())

        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (id, provider, encrypted_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    encrypted_key = excluded.encrypted_key,
                    updated_at = excluded.updated_at
                """,
                (key_id, provider, encrypted_key, now, now),
            )

    def get_api_key(self, provider: str) -> str | None:
        """Get an encrypted API key.

        Args:
            provider: Provider name

        Returns:
            Encrypted key string, or None if not found.
        """
        with self.connection() as conn:
            cursor = conn.execute(
                "SELECT encrypted_key FROM api_keys WHERE provider = ?",
                (provider,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def delete_api_key(self, provider: str) -> bool:
        """Delete an API key."""
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM api_keys WHERE provider = ?", (provider,))
            return cursor.rowcount > 0

    def list_api_key_providers(self) -> list[str]:
        """List all providers with stored API keys.

        Returns:
            List of provider names.
        """
        with self.connection() as conn:
            cursor = conn.execute("SELECT provider FROM api_keys")
            return [row[0] for row in cursor.fetchall()]


def _now() -> str:
    """Get current timestamp as ISO string."""
    return datetime.utcnow().isoformat()


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert SQLite row to dictionary, parsing JSON fields."""
    if row is None:
        return None

    result = dict(row)

    # Parse JSON fields
    for json_field in ["config_json", "metadata_json", "sources_json"]:
        if json_field in result and result[json_field]:
            # Create a new key without _json suffix
            base_key = json_field.replace("_json", "")
            result[base_key] = json.loads(result[json_field])
            del result[json_field]
        elif json_field in result:
            del result[json_field]

    return result
