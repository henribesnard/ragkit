"""Tests for DocumentMetadata and MetadataExtractor."""

from __future__ import annotations

from ragkit.ingestion.metadata import DocumentMetadata
from ragkit.ingestion.metadata_extractor import MetadataExtractor
from ragkit.ingestion.parsers.base import DocumentSection, ParsedDocument
from ragkit.ingestion.sources.base import RawDocument


class TestDocumentMetadata:
    """Tests for the DocumentMetadata Pydantic model."""

    def test_creation_with_defaults(self):
        meta = DocumentMetadata()
        assert meta.tenant == "default"
        assert meta.domain == "general"
        assert meta.confidentiality == "internal"
        assert meta.status == "published"
        assert meta.document_id  # auto-generated UUID
        assert meta.ingested_at is not None
        assert meta.tags == []
        assert meta.custom == {}

    def test_creation_with_custom_values(self):
        meta = DocumentMetadata(
            tenant="acme",
            domain="legal",
            title="My Document",
            source="doc.pdf",
            source_path="/tmp/doc.pdf",
            source_type="pdf",
            language="fr",
            word_count=1000,
            tags=["important"],
            confidentiality="confidential",
        )
        assert meta.tenant == "acme"
        assert meta.domain == "legal"
        assert meta.title == "My Document"
        assert meta.language == "fr"
        assert meta.word_count == 1000
        assert meta.confidentiality == "confidential"
        assert "important" in meta.tags

    def test_to_flat_dict(self):
        meta = DocumentMetadata(
            title="Test",
            source="test.txt",
            source_path="/test.txt",
            source_type="txt",
            word_count=42,
        )
        flat = meta.to_flat_dict()
        assert flat["title"] == "Test"
        assert flat["word_count"] == 42
        assert "custom" not in flat
        assert "parsing_warnings" not in flat
        # ingested_at should be serialised as ISO string
        assert isinstance(flat["ingested_at"], str)

    def test_to_flat_dict_excludes_none(self):
        meta = DocumentMetadata()
        flat = meta.to_flat_dict()
        assert "author" not in flat
        assert "language" not in flat


class TestMetadataExtractor:
    """Tests for MetadataExtractor auto-detection."""

    def _make_raw(self, path: str = "docs/report.pdf", metadata: dict | None = None) -> RawDocument:
        return RawDocument(
            content=b"raw content",
            source_path=path,
            file_type=path.rsplit(".", 1)[-1] if "." in path else "",
            metadata=metadata or {},
        )

    def _make_parsed(
        self, content: str = "", sections: list[DocumentSection] | None = None
    ) -> ParsedDocument:
        return ParsedDocument(content=content, structure=sections)

    def test_extract_basic(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("docs/report.pdf")
        parsed = self._make_parsed("This is the content of the report")

        meta = extractor.extract(raw, parsed)
        assert meta.source == "report.pdf"
        assert meta.source_path == "docs/report.pdf"
        assert meta.source_type == "pdf"
        assert meta.word_count == 7
        assert meta.char_count == 33
        assert meta.document_id  # UUID generated

    def test_title_from_h1_section(self):
        extractor = MetadataExtractor()
        sections = [DocumentSection(title="My Great Title", level=1, content="...")]
        raw = self._make_raw("doc.md")
        parsed = self._make_parsed("# My Great Title\n\nContent here", sections)

        meta = extractor.extract(raw, parsed)
        assert meta.title == "My Great Title"

    def test_title_from_first_line(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("notes.txt")
        parsed = self._make_parsed("# Quick Notes\n\nSome content here")

        meta = extractor.extract(raw, parsed)
        assert meta.title == "Quick Notes"

    def test_title_fallback_to_filename(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("data.csv")
        # Content whose first line contains a period, so it won't be picked as title
        parsed = self._make_parsed("This is a sentence. And another one.\nval1,val2\nval3,val4")

        meta = extractor.extract(raw, parsed)
        assert meta.title == "data"

    def test_author_from_metadata(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.pdf", metadata={"author": "John Doe"})
        parsed = self._make_parsed("Content")

        meta = extractor.extract(raw, parsed)
        assert meta.author == "John Doe"

    def test_author_not_found(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.txt")
        parsed = self._make_parsed("Content")

        meta = extractor.extract(raw, parsed)
        assert meta.author is None

    def test_language_detection(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.txt")
        # Long enough text for langdetect
        text = (
            "This is a sample text in English that is long enough to trigger "
            "language detection in the metadata extraction pipeline."
        )
        parsed = self._make_parsed(text)

        meta = extractor.extract(raw, parsed)
        assert meta.language == "en"

    def test_language_detection_short_text(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.txt")
        parsed = self._make_parsed("Short")

        meta = extractor.extract(raw, parsed)
        assert meta.language is None

    def test_content_counting(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.md")
        content = "Hello world\n\n| col1 | col2 |\n\n```python\nprint('hi')\n```\n\n![img](url)"
        parsed = self._make_parsed(content)

        meta = extractor.extract(raw, parsed)
        assert meta.word_count > 0
        assert meta.char_count > 0
        assert meta.has_tables is True
        assert meta.has_code is True
        assert meta.has_images is True

    def test_mime_type_detection(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.pdf")
        parsed = self._make_parsed("Content")

        meta = extractor.extract(raw, parsed)
        assert meta.mime_type == "application/pdf"

    def test_defaults_applied(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.txt")
        parsed = self._make_parsed("Content")

        meta = extractor.extract(
            raw,
            parsed,
            defaults={
                "tenant": "acme",
                "domain": "legal",
                "tags": ["contract"],
                "confidentiality": "confidential",
            },
        )
        assert meta.tenant == "acme"
        assert meta.domain == "legal"
        assert meta.tags == ["contract"]
        assert meta.confidentiality == "confidential"

    def test_timestamps_from_raw_metadata(self):
        extractor = MetadataExtractor()
        raw = self._make_raw("doc.txt", metadata={"modified_time": 1700000000.0})
        parsed = self._make_parsed("Content")

        meta = extractor.extract(raw, parsed)
        assert meta.modified_at is not None
        assert meta.modified_at.year >= 2023
