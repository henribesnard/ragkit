"""Advanced embedder with cache, rate limiting, retry, and optimizations."""

from __future__ import annotations

import asyncio
import hashlib
from typing import Protocol

import numpy as np

from ragkit.config.schema_v2 import EmbeddingConfigV2
from ragkit.embedding.rate_limiter import RateLimiter


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            np.ndarray of shape (len(texts), dimensions)
        """
        ...


class AdvancedEmbedder:
    """Embedder with all advanced features.

    Features:
    - Multi-provider support (OpenAI, Cohere, HuggingFace, etc.)
    - MD5 cache to avoid re-computation
    - Rate limiting (RPM/TPM)
    - Automatic retry with exponential backoff
    - Intelligent batching
    - L2 normalization
    - Dimensionality reduction (PCA/UMAP)
    - Quantization (float16/int8)
    """

    def __init__(self, config: EmbeddingConfigV2):
        """Initialize the embedder.

        Args:
            config: Complete embedding configuration
        """
        self.config = config

        # Rate limiter
        self.rate_limiter = RateLimiter(
            rpm=config.rate_limit_rpm,
            tpm=config.rate_limit_tpm,
        )

        # Cache
        self.cache: dict[str, np.ndarray] = {} if config.cache_embeddings else None

        # Dimensionality reduction model (lazy init)
        self._reduction_model = None

        # Provider (lazy init)
        self._provider: EmbeddingProvider | None = None

    async def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts with advanced management.

        Workflow:
        1. Preprocessing (strip, normalize)
        2. Truncation if necessary
        3. Cache lookup (MD5 hash)
        4. Rate limiting (RPM/TPM)
        5. API call with retry
        6. Post-processing (normalization, reduction, quantization)
        7. Cache store

        Args:
            texts: List of texts to embed

        Returns:
            np.ndarray of shape (len(texts), dimensions)
        """
        if not texts:
            return np.array([])

        # Step 1: Preprocessing
        processed_texts = [self._preprocess_text(t) for t in texts]

        # Step 2: Truncation if necessary
        processed_texts = [self._truncate_text(t) for t in processed_texts]

        # Step 3: Cache lookup
        embeddings = []
        texts_to_embed = []
        cache_keys = []

        for text in processed_texts:
            cache_key = self._get_cache_key(text)

            if self.cache is not None and cache_key in self.cache:
                # Cache hit
                embeddings.append(self.cache[cache_key])
                cache_keys.append(None)
            else:
                # Cache miss
                embeddings.append(None)
                texts_to_embed.append(text)
                cache_keys.append(cache_key)

        # Step 4-6: Embed non-cached texts
        if texts_to_embed:
            # Rate limiting
            total_tokens = sum(len(t.split()) for t in texts_to_embed)
            await self.rate_limiter.acquire(total_tokens)

            # API call with retry
            new_embeddings = await self._embed_with_retry(texts_to_embed)

            # Normalization
            if self.config.normalize_embeddings:
                new_embeddings = self._normalize(new_embeddings)

            # Dimensionality reduction
            if self.config.dimensionality_reduction != "none":
                new_embeddings = await self._reduce_dimensions(new_embeddings)

            # Convert dtype
            if self.config.embedding_dtype == "float16":
                new_embeddings = new_embeddings.astype(np.float16)
            elif self.config.embedding_dtype == "int8":
                new_embeddings = self._quantize_int8(new_embeddings)

            # Step 7: Cache store
            if self.cache is not None:
                new_idx = 0
                for i, cache_key in enumerate(cache_keys):
                    if cache_key is not None:
                        self.cache[cache_key] = new_embeddings[new_idx]
                        new_idx += 1

            # Combine with cache
            new_idx = 0
            for i in range(len(embeddings)):
                if embeddings[i] is None:
                    embeddings[i] = new_embeddings[new_idx]
                    new_idx += 1

        return np.array(embeddings)

    async def embed_query(self, query: str) -> np.ndarray:
        """Embed a query (can use a different model).

        Args:
            query: Query to embed

        Returns:
            np.ndarray of shape (dimensions,)
        """
        # Use query_model if configured
        if self.config.use_separate_query_model:
            # TODO: Implement separate query model support
            pass

        # Add instruction prefix if configured
        if self.config.query_instruction_prefix:
            query = f"{self.config.query_instruction_prefix}{query}"

        embeddings = await self.embed_batch([query])
        return embeddings[0]

    async def _embed_with_retry(self, texts: list[str]) -> np.ndarray:
        """Embed with automatic retry.

        Args:
            texts: Texts to embed

        Returns:
            np.ndarray of shape (len(texts), dimensions)

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(self.config.max_retries):
            try:
                return await self._call_embedding_api(texts)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    # Last retry, propagate error
                    raise

                # Exponential backoff
                wait_time = self.config.retry_delay * (2**attempt)
                print(
                    f"Embedding failed (attempt {attempt + 1}/{self.config.max_retries}), "
                    f"retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)

        # Should never reach here
        raise RuntimeError("Retry logic error")

    async def _call_embedding_api(self, texts: list[str]) -> np.ndarray:
        """Call the embedding API based on provider.

        Args:
            texts: Texts to embed

        Returns:
            np.ndarray of shape (len(texts), dimensions)
        """
        if self._provider is None:
            self._provider = self._create_provider()

        return await self._provider.embed(texts)

    def _create_provider(self) -> EmbeddingProvider:
        """Create the embedding provider based on configuration.

        Returns:
            Embedding provider
        """
        if self.config.provider == "openai":
            from ragkit.embedding.providers.openai_embedder import OpenAIEmbeddingProvider

            return OpenAIEmbeddingProvider(self.config)

        elif self.config.provider == "cohere":
            from ragkit.embedding.providers.cohere_provider import CohereEmbeddingProvider

            return CohereEmbeddingProvider(self.config)

        elif self.config.provider == "sentence_transformers":
            from ragkit.embedding.providers.sentence_transformers_provider import (
                SentenceTransformersProvider,
            )

            return SentenceTransformersProvider(self.config)

        elif self.config.provider == "huggingface":
            from ragkit.embedding.providers.huggingface_provider import HuggingFaceEmbeddingProvider

            return HuggingFaceEmbeddingProvider(self.config)

        elif self.config.provider == "ollama":
            from ragkit.embedding.providers.ollama_provider import OllamaEmbeddingProvider

            return OllamaEmbeddingProvider(self.config)

        else:
            raise ValueError(f"Unknown embedding provider: {self.config.provider}")

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding.

        Args:
            text: Raw text

        Returns:
            Preprocessed text
        """
        # Strip whitespace
        text = text.strip()

        # Replace multiple spaces with single space
        text = " ".join(text.split())

        return text

    def _truncate_text(self, text: str) -> str:
        """Truncate text according to configured strategy.

        Args:
            text: Text to truncate

        Returns:
            Truncated text
        """
        # Simplification: count words as proxy for tokens
        # In production, use tiktoken for exact token counting
        words = text.split()

        if len(words) <= self.config.max_tokens_per_chunk:
            return text

        if self.config.truncation_strategy == "start":
            # Keep beginning
            return " ".join(words[: self.config.max_tokens_per_chunk])

        elif self.config.truncation_strategy == "end":
            # Keep end
            return " ".join(words[-self.config.max_tokens_per_chunk :])

        elif self.config.truncation_strategy == "middle":
            # Keep beginning + end
            half = self.config.max_tokens_per_chunk // 2
            return " ".join(words[:half] + ["..."] + words[-half:])

        elif self.config.truncation_strategy == "split":
            # This strategy should be handled upstream (chunking)
            # Fallback: keep beginning
            return " ".join(words[: self.config.max_tokens_per_chunk])

        return text

    async def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        """Reduce dimensionality of embeddings.

        Args:
            embeddings: Original embeddings (N, D_original)

        Returns:
            Reduced embeddings (N, D_reduced)
        """
        target_dims = self.config.reduction_target_dims
        if target_dims is None:
            return embeddings

        n_samples, n_features = embeddings.shape
        effective_dims = min(target_dims, n_samples, n_features)

        if self._reduction_model is None or getattr(
            self._reduction_model, "n_components", None
        ) != effective_dims:
            if self.config.dimensionality_reduction == "pca":
                from sklearn.decomposition import PCA

                self._reduction_model = PCA(n_components=effective_dims)
                # Fit on this batch (ideally, fit on larger sample)
                self._reduction_model.fit(embeddings)

            elif self.config.dimensionality_reduction == "umap":
                from umap import UMAP

                self._reduction_model = UMAP(
                    n_components=effective_dims,
                    metric="cosine",
                )
                # UMAP requires fit
                self._reduction_model.fit(embeddings)

        reduced = self._reduction_model.transform(embeddings)
        if effective_dims < target_dims:
            reduced = np.pad(
                reduced,
                ((0, 0), (0, target_dims - effective_dims)),
                mode="constant",
            )
        return reduced

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalization of embeddings (norm = 1).

        Required for cosine distance.

        Args:
            embeddings: Embeddings to normalize (N, D)

        Returns:
            Normalized embeddings (N, D)
        """
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def _quantize_int8(self, embeddings: np.ndarray) -> np.ndarray:
        """int8 quantization to save RAM.

        Transforms float32 [-1, 1] to int8 [-127, 127].

        Args:
            embeddings: float32 embeddings

        Returns:
            int8 embeddings (note: precision loss ~1-2%)
        """
        # Normalize to [-1, 1] if not already done
        min_val = embeddings.min()
        max_val = embeddings.max()

        # Scale to [-127, 127]
        scale = 127.0 / max(abs(min_val), abs(max_val))

        quantized = (embeddings * scale).astype(np.int8)

        # Store scale factor for de-quantization later
        # (TODO: implement scale factor storage)

        return quantized

    def _get_cache_key(self, text: str) -> str:
        """Generate MD5 cache key for a text.

        Args:
            text: Text to hash

        Returns:
            MD5 hash (32 hex characters)
        """
        return hashlib.md5(text.encode("utf-8")).hexdigest()
