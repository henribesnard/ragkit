import pytest

from ragkit.config.schema import ParsingConfig
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
        content="Plain text".encode("utf-8"),
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
