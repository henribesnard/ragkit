"""Tests for ONNX local embedding provider."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ragkit.config.schema import EmbeddingModelConfig, EmbeddingParams
from ragkit.onnx.download_manager import (
    SUPPORTED_MODELS,
    ModelDownloadManager,
    get_model_dimensions,
)

# --- Unit Tests for ModelDownloadManager ---


def test_supported_models_have_required_fields():
    """Verify all supported models have required metadata."""
    required_fields = {"repo_id", "dimensions", "size_mb", "description", "files"}
    for model_id, info in SUPPORTED_MODELS.items():
        missing = required_fields - set(info.keys())
        assert not missing, f"Model {model_id} missing fields: {missing}"


def test_get_model_dimensions():
    """Test get_model_dimensions returns correct dimensions."""
    assert get_model_dimensions("all-MiniLM-L6-v2") == 384
    assert get_model_dimensions("all-mpnet-base-v2") == 768

    with pytest.raises(ValueError, match="Unknown model"):
        get_model_dimensions("nonexistent-model")


def test_download_manager_init(tmp_path: Path):
    """Test ModelDownloadManager initialization."""
    manager = ModelDownloadManager(cache_dir=tmp_path)
    assert manager.cache_dir == tmp_path
    assert manager.cache_dir.exists()


def test_download_manager_get_model_path_not_downloaded(tmp_path: Path):
    """Test get_model_path returns None for non-downloaded model."""
    manager = ModelDownloadManager(cache_dir=tmp_path)
    assert manager.get_model_path("all-MiniLM-L6-v2") is None


def test_download_manager_get_model_path_downloaded(tmp_path: Path):
    """Test get_model_path returns path for downloaded model."""
    manager = ModelDownloadManager(cache_dir=tmp_path)

    # Simulate downloaded model
    model_dir = tmp_path / "all-MiniLM-L6-v2"
    model_dir.mkdir()
    (model_dir / "model.onnx").touch()

    path = manager.get_model_path("all-MiniLM-L6-v2")
    assert path == model_dir


def test_download_manager_list_downloaded(tmp_path: Path):
    """Test list_downloaded_models returns correct list."""
    manager = ModelDownloadManager(cache_dir=tmp_path)

    # Initially empty
    assert manager.list_downloaded_models() == []

    # Add a model
    model_dir = tmp_path / "all-MiniLM-L6-v2"
    model_dir.mkdir()
    (model_dir / "model.onnx").touch()

    downloaded = manager.list_downloaded_models()
    assert "all-MiniLM-L6-v2" in downloaded


def test_download_manager_list_available(tmp_path: Path):
    """Test list_available_models returns all supported models."""
    manager = ModelDownloadManager(cache_dir=tmp_path)
    available = manager.list_available_models()

    assert len(available) == len(SUPPORTED_MODELS)
    for model in available:
        assert "id" in model
        assert "dimensions" in model
        assert "downloaded" in model
        assert model["downloaded"] is False  # Nothing downloaded yet


def test_download_manager_delete_model(tmp_path: Path):
    """Test delete_model removes model directory."""
    manager = ModelDownloadManager(cache_dir=tmp_path)

    # Create fake model
    model_dir = tmp_path / "all-MiniLM-L6-v2"
    model_dir.mkdir()
    (model_dir / "model.onnx").touch()

    assert manager.delete_model("all-MiniLM-L6-v2") is True
    assert not model_dir.exists()

    # Deleting non-existent model returns False
    assert manager.delete_model("nonexistent") is False


def test_download_manager_cache_size(tmp_path: Path):
    """Test get_cache_size_mb calculation."""
    manager = ModelDownloadManager(cache_dir=tmp_path)

    # Create file with known size
    model_dir = tmp_path / "all-MiniLM-L6-v2"
    model_dir.mkdir()
    (model_dir / "model.onnx").write_bytes(b"0" * 1024 * 1024)  # 1 MB

    size = manager.get_cache_size_mb()
    assert 0.9 < size < 1.1  # ~1 MB


# --- Unit Tests for ONNXLocalEmbedder (mocked) ---


@pytest.fixture
def onnx_config():
    """Create ONNX embedding config fixture."""
    return EmbeddingModelConfig(
        provider="onnx_local",
        model="all-MiniLM-L6-v2",
        params=EmbeddingParams(batch_size=32),
    )


def test_onnx_embedder_init_valid_model(onnx_config):
    """Test ONNXLocalEmbedder initialization with valid model."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    embedder = ONNXLocalEmbedder(onnx_config)
    assert embedder.model_id == "all-MiniLM-L6-v2"
    assert embedder.dimensions == 384
    assert embedder._batch_size == 32


def test_onnx_embedder_init_invalid_model():
    """Test ONNXLocalEmbedder raises error for invalid model."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    config = EmbeddingModelConfig(
        provider="onnx_local",
        model="nonexistent-model",
    )

    with pytest.raises(ValueError, match="Unsupported ONNX model"):
        ONNXLocalEmbedder(config)


def test_onnx_embedder_dimensions(onnx_config):
    """Test dimensions property returns correct value."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    embedder = ONNXLocalEmbedder(onnx_config)
    assert embedder.dimensions == 384


def test_onnx_embedder_get_model_info(onnx_config):
    """Test get_model_info returns correct metadata."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    embedder = ONNXLocalEmbedder(onnx_config)
    info = embedder.get_model_info()

    assert info["model_id"] == "all-MiniLM-L6-v2"
    assert info["dimensions"] == 384
    assert info["batch_size"] == 32
    assert info["initialized"] is False


@pytest.mark.asyncio
async def test_onnx_embedder_embed_empty_list(onnx_config):
    """Test embed() with empty list returns empty list."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    embedder = ONNXLocalEmbedder(onnx_config)
    result = await embedder.embed([])
    assert result == []


@pytest.mark.asyncio
async def test_onnx_embedder_mean_pooling():
    """Test _mean_pooling implementation."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    config = EmbeddingModelConfig(
        provider="onnx_local",
        model="all-MiniLM-L6-v2",
    )
    embedder = ONNXLocalEmbedder(config)

    # Test with simple inputs
    hidden_states = np.array(
        [
            [[1.0, 2.0], [3.0, 4.0], [0.0, 0.0]],  # batch 1, seq_len 3, hidden 2
        ]
    )
    attention_mask = np.array([[1, 1, 0]])  # Only first 2 tokens are real

    pooled = embedder._mean_pooling(hidden_states, attention_mask)

    # Mean of [1,2] and [3,4] = [2, 3]
    expected = np.array([[2.0, 3.0]])
    np.testing.assert_array_almost_equal(pooled, expected)


@pytest.mark.asyncio
async def test_onnx_embedder_normalize():
    """Test _normalize implementation."""
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    config = EmbeddingModelConfig(
        provider="onnx_local",
        model="all-MiniLM-L6-v2",
    )
    embedder = ONNXLocalEmbedder(config)

    embeddings = np.array([[3.0, 4.0]])  # Length = 5
    normalized = embedder._normalize(embeddings)

    # Should be [0.6, 0.8]
    expected = np.array([[0.6, 0.8]])
    np.testing.assert_array_almost_equal(normalized, expected)

    # Verify unit norm
    norm = np.linalg.norm(normalized, axis=1)
    np.testing.assert_array_almost_equal(norm, [1.0])


# --- Integration Tests (require onnxruntime + tokenizers) ---


@pytest.fixture
def has_onnx_deps():
    """Check if ONNX dependencies are available."""
    try:
        import onnxruntime  # noqa: F401
        import tokenizers  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_onnx_embedder_integration(onnx_config, has_onnx_deps, tmp_path):
    """Integration test with real ONNX model (requires dependencies)."""
    if not has_onnx_deps:
        pytest.skip("ONNX dependencies not installed")

    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    # Use temp directory for model cache
    download_manager = ModelDownloadManager(cache_dir=tmp_path)
    embedder = ONNXLocalEmbedder(onnx_config, download_manager=download_manager)

    # This will trigger model download if not cached
    texts = ["Hello world", "This is a test"]
    embeddings = await embedder.embed(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384  # all-MiniLM-L6-v2 dimensions
    assert all(isinstance(x, float) for x in embeddings[0])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_onnx_embedder_query_integration(onnx_config, has_onnx_deps, tmp_path):
    """Integration test for embed_query (requires dependencies)."""
    if not has_onnx_deps:
        pytest.skip("ONNX dependencies not installed")

    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    download_manager = ModelDownloadManager(cache_dir=tmp_path)
    embedder = ONNXLocalEmbedder(onnx_config, download_manager=download_manager)

    query_embedding = await embedder.embed_query("What is the meaning of life?")

    assert len(query_embedding) == 384
    assert all(isinstance(x, float) for x in query_embedding)


# --- Factory Tests ---


def test_create_embedder_onnx_local():
    """Test create_embedder factory with onnx_local provider."""
    from ragkit.embedding import create_embedder
    from ragkit.embedding.providers.onnx_local import ONNXLocalEmbedder

    config = EmbeddingModelConfig(
        provider="onnx_local",
        model="all-MiniLM-L6-v2",
    )

    embedder = create_embedder(config)
    assert isinstance(embedder, ONNXLocalEmbedder)
