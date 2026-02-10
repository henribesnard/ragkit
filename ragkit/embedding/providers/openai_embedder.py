"""OpenAI embedding provider for EmbeddingConfigV2."""

from __future__ import annotations

import os
from typing import Any

import numpy as np
from openai import AsyncOpenAI

from ragkit.config.schema_v2 import EmbeddingConfigV2


class OpenAIEmbeddingProvider:
    """Provider for OpenAI text-embedding-3-* models."""

    def __init__(self, config: EmbeddingConfigV2):
        """Initialize the OpenAI provider.

        Args:
            config: Embedding configuration
        """
        self.config = config

        # OpenAI client
        api_key = config.api_key or self._get_api_key_from_env()
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.api_base_url,
            timeout=config.timeout,
        )

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts via OpenAI API.

        Args:
            texts: Texts to embed (max 2048 according to OpenAI)

        Returns:
            np.ndarray of shape (len(texts), dimensions)
        """
        # Add instruction prefix if configured
        if self.config.document_instruction_prefix:
            texts = [f"{self.config.document_instruction_prefix}{t}" for t in texts]

        # API call
        payload: dict[str, Any] = {
            "model": self.config.model,
            "input": texts,
            "encoding_format": "float",  # or "base64" for less bandwidth
        }
        if self.config.dimensions is not None:
            payload["dimensions"] = self.config.dimensions

        response = await self.client.embeddings.create(**payload)

        # Extract embeddings
        embeddings = [item.embedding for item in response.data]

        return np.array(embeddings, dtype=np.float32)

    def _get_api_key_from_env(self) -> str:
        """Retrieve API key from environment variable.

        Returns:
            API key

        Raises:
            ValueError: If environment variable doesn't exist
        """
        env_var = self.config.api_key_env or "OPENAI_API_KEY"
        api_key = os.getenv(env_var)

        if not api_key:
            raise ValueError(
                f"API key not found. Set {env_var} environment variable "
                f"or provide api_key in config."
            )

        return api_key
