import pytest

from ragkit.config.schema import LocalSourceConfig
from ragkit.ingestion.sources.local import LocalSourceLoader


@pytest.fixture
def sample_files(tmp_path):
    (tmp_path / "doc1.pdf").write_bytes(b"PDF content")
    (tmp_path / "doc2.md").write_text("# Markdown")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "doc3.txt").write_text("Text content")
    return tmp_path


@pytest.mark.asyncio
async def test_local_loader_finds_files(sample_files):
    config = LocalSourceConfig(
        type="local",
        path=str(sample_files),
        patterns=["*.pdf", "*.md", "*.txt"],
        recursive=True,
    )
    loader = LocalSourceLoader(config)

    docs = [doc async for doc in loader.load()]
    assert len(docs) == 3


@pytest.mark.asyncio
async def test_local_loader_respects_patterns(sample_files):
    config = LocalSourceConfig(
        type="local",
        path=str(sample_files),
        patterns=["*.pdf"],
        recursive=True,
    )
    loader = LocalSourceLoader(config)

    docs = [doc async for doc in loader.load()]
    assert len(docs) == 1
    assert docs[0].file_type == "pdf"
