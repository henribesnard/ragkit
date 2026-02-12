"""Tests for DocumentDeduplicator."""

from __future__ import annotations

from ragkit.ingestion.deduplication import DocumentDeduplicator


class TestDocumentDeduplicator:
    """Tests for document-level deduplication."""

    def test_exact_dedup_detects_duplicate(self):
        dedup = DocumentDeduplicator(strategy="exact")
        content = "This is a test document with some content."
        dedup.register(content)
        assert dedup.is_duplicate(content) is True

    def test_exact_dedup_normalises_whitespace(self):
        dedup = DocumentDeduplicator(strategy="exact")
        dedup.register("hello   world")
        # Same content with different whitespace should be detected
        assert dedup.is_duplicate("hello world") is True

    def test_exact_dedup_non_duplicate(self):
        dedup = DocumentDeduplicator(strategy="exact")
        dedup.register("First document content")
        assert dedup.is_duplicate("Different document content") is False

    def test_fuzzy_dedup_detects_near_duplicate(self):
        dedup = DocumentDeduplicator(strategy="fuzzy", threshold=0.8)
        original = "The quick brown fox jumps over the lazy dog"
        dedup.register(original)
        # Very similar text
        similar = "The quick brown fox jumps over the lazy cat"
        assert dedup.is_duplicate(similar) is True

    def test_fuzzy_dedup_non_duplicate(self):
        dedup = DocumentDeduplicator(strategy="fuzzy", threshold=0.8)
        dedup.register("The quick brown fox jumps over the lazy dog")
        assert dedup.is_duplicate("A completely different text about something else") is False

    def test_none_strategy_never_detects(self):
        dedup = DocumentDeduplicator(strategy="none")
        dedup.register("test content")
        assert dedup.is_duplicate("test content") is False

    def test_unknown_strategy_never_detects(self):
        dedup = DocumentDeduplicator(strategy="unknown_strategy")
        assert dedup.is_duplicate("anything") is False

    def test_multiple_documents(self):
        dedup = DocumentDeduplicator(strategy="exact")
        dedup.register("Document A")
        dedup.register("Document B")
        dedup.register("Document C")
        assert dedup.is_duplicate("Document A") is True
        assert dedup.is_duplicate("Document B") is True
        assert dedup.is_duplicate("Document D") is False

    def test_reset_clears_registry(self):
        dedup = DocumentDeduplicator(strategy="exact")
        dedup.register("test content")
        assert dedup.is_duplicate("test content") is True
        dedup.reset()
        assert dedup.is_duplicate("test content") is False

    def test_reset_clears_fuzzy_registry(self):
        dedup = DocumentDeduplicator(strategy="fuzzy", threshold=0.8)
        dedup.register("test content here")
        dedup.reset()
        assert dedup.is_duplicate("test content here") is False
        assert dedup._texts == []

    def test_exact_hash_is_deterministic(self):
        h1 = DocumentDeduplicator._exact_hash("hello world")
        h2 = DocumentDeduplicator._exact_hash("hello world")
        assert h1 == h2

    def test_exact_hash_differs_for_different_content(self):
        h1 = DocumentDeduplicator._exact_hash("hello world")
        h2 = DocumentDeduplicator._exact_hash("goodbye world")
        assert h1 != h2
