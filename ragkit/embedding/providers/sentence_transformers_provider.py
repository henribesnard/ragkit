"""SentenceTransformers provider for local embeddings."""

from __future__ import annotations

import asyncio

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from ragkit.config.schema_v2 import EmbeddingConfigV2


class SentenceTransformersProvider:
    """Provider for SentenceTransformers (local, free)."""

    def __init__(self, config: EmbeddingConfigV2):
        """Initialize the SentenceTransformers provider.

        Args:
            config: Embedding configuration
        """
        self.config = config

        # Load model
        device = "cuda" if config.use_gpu and torch.cuda.is_available() else "cpu"

        self.model = SentenceTransformer(
            config.model,
            device=device,
        )

        # Half precision if configured (GPU only)
        if config.use_gpu and hasattr(self.model, "half"):
            self.model.half()

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts locally.

        Args:
            texts: Texts to embed

        Returns:
            np.ndarray of shape (len(texts), dimensions)
        """
        # SentenceTransformers encode is synchronous, run in executor
        loop = asyncio.get_event_loop()

        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=self.config.normalize_embeddings,
            ),
        )

        return embeddings
