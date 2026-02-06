"""ONNX local embedding provider for 100% offline embedding generation.

This provider uses ONNX Runtime to run embedding models locally without
any external API calls, enabling fully private and offline RAG pipelines.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.exceptions import EmbeddingError
from ragkit.onnx.download_manager import (
    SUPPORTED_MODELS,
    ModelDownloadManager,
    get_model_dimensions,
)

if TYPE_CHECKING:
    import onnxruntime as ort
    from tokenizers import Tokenizer

logger = logging.getLogger(__name__)


class ONNXLocalEmbedder(BaseEmbedder):
    """Local embedding provider using ONNX Runtime.

    This embedder runs transformer models locally using ONNX Runtime,
    enabling 100% offline embedding generation without API calls.

    Supported models:
    - all-MiniLM-L6-v2 (384 dim, 90 MB) - default, fast
    - all-mpnet-base-v2 (768 dim, 420 MB) - higher quality
    - multilingual-e5-small (384 dim, 470 MB) - multilingual
    - bge-small-en-v1.5 (384 dim, 130 MB) - retrieval optimized
    """

    def __init__(
        self,
        config: EmbeddingModelConfig,
        download_manager: ModelDownloadManager | None = None,
    ):
        """Initialize the ONNX embedder.

        Args:
            config: Embedding model configuration.
            download_manager: Optional custom download manager.
        """
        self.config = config
        self.model_id = config.model
        self._download_manager = download_manager or ModelDownloadManager()

        # Validate model is supported
        if self.model_id not in SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported ONNX model: {self.model_id}. "
                f"Supported: {list(SUPPORTED_MODELS.keys())}"
            )

        self._dimensions = get_model_dimensions(self.model_id)
        self._batch_size = config.params.batch_size or 32

        # Lazy-loaded components
        self._session: ort.InferenceSession | None = None
        self._tokenizer: Tokenizer | None = None
        self._model_path: Path | None = None
        self._initialized = False

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions for the current model."""
        return self._dimensions

    async def _ensure_initialized(self) -> None:
        """Ensure model is downloaded and loaded.

        Downloads the model if not present, then loads it into memory.
        """
        if self._initialized:
            return

        # Download model if needed
        model_path = self._download_manager.get_model_path(self.model_id)
        if not model_path:
            logger.info(f"Downloading ONNX model: {self.model_id}")
            model_path = await self._download_manager.download_model(self.model_id)

        self._model_path = model_path

        # Load in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
        self._initialized = True

    def _load_model(self) -> None:
        """Load ONNX model and tokenizer (sync, called in executor)."""
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as e:
            raise EmbeddingError(
                "ONNX dependencies not installed. "
                "Install with: pip install ragkit[desktop]"
            ) from e

        model_path = self._model_path
        if not model_path:
            raise EmbeddingError("Model path not set")

        onnx_path = model_path / "model.onnx"
        tokenizer_path = model_path / "tokenizer.json"

        if not onnx_path.exists():
            raise EmbeddingError(f"ONNX model not found: {onnx_path}")
        if not tokenizer_path.exists():
            raise EmbeddingError(f"Tokenizer not found: {tokenizer_path}")

        # Create ONNX session with optimizations
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        sess_options.intra_op_num_threads = 4

        # Use CPU provider (most compatible)
        providers = ["CPUExecutionProvider"]

        self._session = ort.InferenceSession(
            str(onnx_path),
            sess_options=sess_options,
            providers=providers,
        )

        self._tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        self._tokenizer.enable_truncation(max_length=512)

        logger.info(f"Loaded ONNX model: {self.model_id}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not texts:
            return []

        await self._ensure_initialized()

        try:
            # Process in batches
            all_embeddings: list[list[float]] = []

            for start in range(0, len(texts), self._batch_size):
                batch = texts[start : start + self._batch_size]
                batch_embeddings = await self._embed_batch(batch)
                all_embeddings.extend(batch_embeddings)

            return all_embeddings

        except Exception as e:
            raise EmbeddingError(f"ONNX embedding failed: {e}") from e

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts (runs inference in executor)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_batch_sync, texts)

    def _embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous batch embedding (called in executor)."""
        if not self._tokenizer or not self._session:
            raise EmbeddingError("Model not loaded")

        # Tokenize batch
        encoded = self._tokenizer.encode_batch(texts)

        # Prepare inputs
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)

        # Handle token_type_ids if model expects it
        input_names = [inp.name for inp in self._session.get_inputs()]
        feeds = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        if "token_type_ids" in input_names:
            token_type_ids = np.zeros_like(input_ids, dtype=np.int64)
            feeds["token_type_ids"] = token_type_ids

        # Run inference
        outputs = self._session.run(None, feeds)

        # Get embeddings - output is typically (batch, seq_len, hidden_dim)
        # We need to pool to get (batch, hidden_dim)
        last_hidden_state = outputs[0]  # (batch, seq_len, hidden_dim)

        # Mean pooling over sequence (excluding padding)
        embeddings = self._mean_pooling(last_hidden_state, attention_mask)

        # Normalize embeddings
        embeddings = self._normalize(embeddings)

        return embeddings.tolist()

    def _mean_pooling(
        self,
        hidden_states: np.ndarray,
        attention_mask: np.ndarray,
    ) -> np.ndarray:
        """Apply mean pooling to hidden states.

        Args:
            hidden_states: Shape (batch, seq_len, hidden_dim)
            attention_mask: Shape (batch, seq_len)

        Returns:
            Pooled embeddings of shape (batch, hidden_dim)
        """
        # Expand attention mask for broadcasting
        mask_expanded = np.expand_dims(attention_mask, axis=-1)
        mask_expanded = np.broadcast_to(mask_expanded, hidden_states.shape)

        # Sum hidden states where attention_mask is 1
        sum_embeddings = np.sum(hidden_states * mask_expanded, axis=1)

        # Sum of attention mask (number of real tokens per sequence)
        sum_mask = np.sum(mask_expanded, axis=1)
        sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)  # Avoid division by zero

        return sum_embeddings / sum_mask

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalize embeddings."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-9, a_max=None)
        return embeddings / norms

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query.

        Args:
            query: Query text to embed.

        Returns:
            Embedding vector.
        """
        results = await self.embed([query])
        return results[0]

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Dictionary with model metadata.
        """
        return {
            "model_id": self.model_id,
            "dimensions": self._dimensions,
            "batch_size": self._batch_size,
            "initialized": self._initialized,
            "model_path": str(self._model_path) if self._model_path else None,
        }
