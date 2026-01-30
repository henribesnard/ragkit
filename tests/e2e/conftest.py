import pytest


@pytest.fixture
def sample_docs(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("# Doc 1\nParis is the capital of France.")
    (docs_dir / "doc2.txt").write_text("This document talks about machine learning.")
    return docs_dir
