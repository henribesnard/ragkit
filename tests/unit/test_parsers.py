import pytest

from ragkit.config.schema import ParsingConfig
from ragkit.ingestion.parsers.docx import DOCXParser
from ragkit.ingestion.parsers.markdown import MarkdownParser
from ragkit.ingestion.parsers.pdf import PDFParser
from ragkit.ingestion.parsers.text import TextParser
from ragkit.ingestion.sources.base import RawDocument


@pytest.mark.asyncio
async def test_markdown_parser_preserves_structure():
    content = """
# Title
## Section 1
Content of section 1.
## Section 2
Content of section 2.
"""
    raw_doc = RawDocument(
        content=content,
        source_path="doc.md",
        file_type="md",
        metadata={},
    )
    parser = MarkdownParser(ParsingConfig())
    result = await parser.parse(raw_doc)

    assert "Title" in result.content
    assert result.structure is not None
    assert len(result.structure) >= 2


@pytest.mark.asyncio
async def test_text_parser_decodes_bytes():
    raw_doc = RawDocument(
        content=b"Plain text",
        source_path="doc.txt",
        file_type="txt",
        metadata={},
    )
    parser = TextParser(ParsingConfig())
    result = await parser.parse(raw_doc)

    assert result.content == "Plain text"


@pytest.mark.asyncio
async def test_pdf_parser_accepts_text_fallback():
    raw_doc = RawDocument(
        content="PDF-like text",
        source_path="sample.pdf",
        file_type="pdf",
        metadata={},
    )
    parser = PDFParser(ParsingConfig())
    result = await parser.parse(raw_doc)

    assert "PDF-like" in result.content


@pytest.mark.asyncio
async def test_docx_parser_parses_docx_bytes(tmp_path):
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    doc.add_paragraph("Hello DOCX")
    doc_path = tmp_path / "sample.docx"
    doc.save(str(doc_path))

    raw_doc = RawDocument(
        content=doc_path.read_bytes(),
        source_path="sample.docx",
        file_type="docx",
        metadata={},
    )
    parser = DOCXParser(ParsingConfig())
    result = await parser.parse(raw_doc)

    assert "Hello DOCX" in result.content
    assert result.metadata.get("file_type") == "docx"


@pytest.mark.asyncio
async def test_doc_parser_fallback_decodes_bytes(monkeypatch):
    import ragkit.ingestion.parsers.docx as docx_module

    monkeypatch.setattr(docx_module, "_extract_with_unstructured", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(docx_module, "_extract_with_antiword", lambda *_args, **_kwargs: None)

    raw_doc = RawDocument(
        content=b"Legacy DOC content",
        source_path="sample.doc",
        file_type="doc",
        metadata={},
    )
    parser = DOCXParser(ParsingConfig())
    result = await parser.parse(raw_doc)

    assert "Legacy DOC content" in result.content
    assert result.metadata.get("file_type") == "doc"
