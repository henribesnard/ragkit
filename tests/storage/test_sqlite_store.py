"""Tests for SQLite storage backend."""

from __future__ import annotations

from pathlib import Path

import pytest

from ragkit.storage.sqlite_store import SQLiteStore


@pytest.fixture
def db(tmp_path: Path) -> SQLiteStore:
    """Create a temporary SQLite store."""
    return SQLiteStore(db_path=tmp_path / "test.db")


# --- Knowledge Base Tests ---


def test_create_knowledge_base(db: SQLiteStore):
    """Test creating a knowledge base."""
    kb = db.create_knowledge_base(
        name="Test KB",
        embedding_model="all-MiniLM-L6-v2",
        embedding_dimensions=384,
        description="A test knowledge base",
    )

    assert kb["id"] is not None
    assert kb["name"] == "Test KB"
    assert kb["embedding_model"] == "all-MiniLM-L6-v2"
    assert kb["embedding_dimensions"] == 384
    assert kb["description"] == "A test knowledge base"
    assert kb["document_count"] == 0
    assert kb["chunk_count"] == 0


def test_create_knowledge_base_duplicate_name(db: SQLiteStore):
    """Test that duplicate names raise an error."""
    db.create_knowledge_base(
        name="Unique Name",
        embedding_model="test",
        embedding_dimensions=384,
    )

    with pytest.raises(Exception):  # sqlite3.IntegrityError
        db.create_knowledge_base(
            name="Unique Name",
            embedding_model="test",
            embedding_dimensions=384,
        )


def test_get_knowledge_base(db: SQLiteStore):
    """Test retrieving a knowledge base."""
    created = db.create_knowledge_base(
        name="Test",
        embedding_model="test",
        embedding_dimensions=384,
    )

    retrieved = db.get_knowledge_base(created["id"])
    assert retrieved is not None
    assert retrieved["id"] == created["id"]
    assert retrieved["name"] == "Test"


def test_get_knowledge_base_not_found(db: SQLiteStore):
    """Test retrieving non-existent knowledge base."""
    result = db.get_knowledge_base("nonexistent-id")
    assert result is None


def test_get_knowledge_base_by_name(db: SQLiteStore):
    """Test retrieving knowledge base by name."""
    db.create_knowledge_base(
        name="Named KB",
        embedding_model="test",
        embedding_dimensions=384,
    )

    result = db.get_knowledge_base_by_name("Named KB")
    assert result is not None
    assert result["name"] == "Named KB"


def test_list_knowledge_bases(db: SQLiteStore):
    """Test listing knowledge bases."""
    db.create_knowledge_base(name="KB1", embedding_model="test", embedding_dimensions=384)
    db.create_knowledge_base(name="KB2", embedding_model="test", embedding_dimensions=384)

    kbs = db.list_knowledge_bases()
    assert len(kbs) == 2
    names = {kb["name"] for kb in kbs}
    assert names == {"KB1", "KB2"}


def test_update_knowledge_base(db: SQLiteStore):
    """Test updating a knowledge base."""
    created = db.create_knowledge_base(
        name="Original",
        embedding_model="test",
        embedding_dimensions=384,
    )

    updated = db.update_knowledge_base(
        created["id"],
        name="Updated",
        description="New description",
        document_count=5,
    )

    assert updated is not None
    assert updated["name"] == "Updated"
    assert updated["description"] == "New description"
    assert updated["document_count"] == 5


def test_delete_knowledge_base(db: SQLiteStore):
    """Test deleting a knowledge base."""
    created = db.create_knowledge_base(
        name="ToDelete",
        embedding_model="test",
        embedding_dimensions=384,
    )

    assert db.delete_knowledge_base(created["id"]) is True
    assert db.get_knowledge_base(created["id"]) is None


def test_delete_knowledge_base_not_found(db: SQLiteStore):
    """Test deleting non-existent knowledge base."""
    assert db.delete_knowledge_base("nonexistent") is False


# --- Document Tests ---


def test_create_document(db: SQLiteStore):
    """Test creating a document."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)

    doc = db.create_document(
        kb_id=kb["id"],
        source_path="/path/to/file.pdf",
        filename="file.pdf",
        file_type="pdf",
        file_size=1024,
    )

    assert doc["id"] is not None
    assert doc["kb_id"] == kb["id"]
    assert doc["source_path"] == "/path/to/file.pdf"
    assert doc["filename"] == "file.pdf"
    assert doc["status"] == "pending"


def test_list_documents(db: SQLiteStore):
    """Test listing documents."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)
    db.create_document(kb_id=kb["id"], source_path="/a.pdf", filename="a.pdf")
    db.create_document(kb_id=kb["id"], source_path="/b.pdf", filename="b.pdf")

    docs = db.list_documents(kb["id"])
    assert len(docs) == 2


def test_list_documents_with_status_filter(db: SQLiteStore):
    """Test listing documents with status filter."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)
    doc1 = db.create_document(kb_id=kb["id"], source_path="/a.pdf", filename="a.pdf")
    db.create_document(kb_id=kb["id"], source_path="/b.pdf", filename="b.pdf")

    db.update_document(doc1["id"], status="indexed")

    indexed = db.list_documents(kb["id"], status="indexed")
    assert len(indexed) == 1
    assert indexed[0]["filename"] == "a.pdf"


def test_update_document(db: SQLiteStore):
    """Test updating a document."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)
    doc = db.create_document(kb_id=kb["id"], source_path="/a.pdf", filename="a.pdf")

    updated = db.update_document(doc["id"], status="indexed", chunk_count=10)

    assert updated is not None
    assert updated["status"] == "indexed"
    assert updated["chunk_count"] == 10


def test_delete_document(db: SQLiteStore):
    """Test deleting a document."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)
    doc = db.create_document(kb_id=kb["id"], source_path="/a.pdf", filename="a.pdf")

    assert db.delete_document(doc["id"]) is True
    assert db.get_document(doc["id"]) is None


def test_cascade_delete_documents(db: SQLiteStore):
    """Test that deleting KB cascades to documents."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)
    doc = db.create_document(kb_id=kb["id"], source_path="/a.pdf", filename="a.pdf")

    db.delete_knowledge_base(kb["id"])

    # Document should be deleted too
    assert db.get_document(doc["id"]) is None


# --- Conversation Tests ---


def test_create_conversation(db: SQLiteStore):
    """Test creating a conversation."""
    conv = db.create_conversation(title="Test Conversation")

    assert conv["id"] is not None
    assert conv["title"] == "Test Conversation"
    assert conv["kb_id"] is None


def test_create_conversation_with_kb(db: SQLiteStore):
    """Test creating a conversation linked to a KB."""
    kb = db.create_knowledge_base(name="KB", embedding_model="test", embedding_dimensions=384)
    conv = db.create_conversation(kb_id=kb["id"], title="KB Conversation")

    assert conv["kb_id"] == kb["id"]


def test_list_conversations(db: SQLiteStore):
    """Test listing conversations."""
    db.create_conversation(title="Conv 1")
    db.create_conversation(title="Conv 2")

    convs = db.list_conversations()
    assert len(convs) == 2


def test_delete_conversation(db: SQLiteStore):
    """Test deleting a conversation."""
    conv = db.create_conversation(title="ToDelete")

    assert db.delete_conversation(conv["id"]) is True
    assert db.get_conversation(conv["id"]) is None


# --- Message Tests ---


def test_create_message(db: SQLiteStore):
    """Test creating a message."""
    conv = db.create_conversation(title="Test")

    msg = db.create_message(
        conversation_id=conv["id"],
        role="user",
        content="Hello!",
    )

    assert msg["id"] is not None
    assert msg["role"] == "user"
    assert msg["content"] == "Hello!"


def test_create_message_with_sources(db: SQLiteStore):
    """Test creating a message with sources."""
    conv = db.create_conversation(title="Test")

    sources = [{"filename": "doc.pdf", "chunk": "Some text"}]
    msg = db.create_message(
        conversation_id=conv["id"],
        role="assistant",
        content="Based on the document...",
        sources=sources,
        latency_ms=150,
    )

    assert msg["sources"] == sources
    assert msg["latency_ms"] == 150


def test_list_messages(db: SQLiteStore):
    """Test listing messages in a conversation."""
    conv = db.create_conversation(title="Test")
    db.create_message(conversation_id=conv["id"], role="user", content="Hi")
    db.create_message(conversation_id=conv["id"], role="assistant", content="Hello")

    messages = db.list_messages(conv["id"])
    assert len(messages) == 2
    assert messages[0]["content"] == "Hi"  # Oldest first
    assert messages[1]["content"] == "Hello"


def test_cascade_delete_messages(db: SQLiteStore):
    """Test that deleting conversation cascades to messages."""
    conv = db.create_conversation(title="Test")
    msg = db.create_message(conversation_id=conv["id"], role="user", content="Hi")

    db.delete_conversation(conv["id"])

    # Message should be deleted too
    assert db.get_message(msg["id"]) is None


# --- Settings Tests ---


def test_set_and_get_setting(db: SQLiteStore):
    """Test setting and getting a setting."""
    db.set_setting("theme", "dark")
    assert db.get_setting("theme") == "dark"


def test_get_setting_default(db: SQLiteStore):
    """Test getting setting with default."""
    assert db.get_setting("nonexistent", "default") == "default"


def test_set_setting_complex_value(db: SQLiteStore):
    """Test setting a complex JSON value."""
    value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
    db.set_setting("complex", value)
    assert db.get_setting("complex") == value


def test_delete_setting(db: SQLiteStore):
    """Test deleting a setting."""
    db.set_setting("temp", "value")
    assert db.delete_setting("temp") is True
    assert db.get_setting("temp") is None


# --- API Key Tests ---


def test_store_and_get_api_key(db: SQLiteStore):
    """Test storing and retrieving an API key."""
    db.store_api_key("openai", "encrypted_key_data")
    assert db.get_api_key("openai") == "encrypted_key_data"


def test_update_api_key(db: SQLiteStore):
    """Test updating an existing API key."""
    db.store_api_key("openai", "old_key")
    db.store_api_key("openai", "new_key")
    assert db.get_api_key("openai") == "new_key"


def test_list_api_key_providers(db: SQLiteStore):
    """Test listing providers with stored keys."""
    db.store_api_key("openai", "key1")
    db.store_api_key("anthropic", "key2")

    providers = db.list_api_key_providers()
    assert set(providers) == {"openai", "anthropic"}


def test_delete_api_key(db: SQLiteStore):
    """Test deleting an API key."""
    db.store_api_key("openai", "key")
    assert db.delete_api_key("openai") is True
    assert db.get_api_key("openai") is None
