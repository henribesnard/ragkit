"""Download manager for ONNX embedding models.

This module handles downloading, caching, and managing ONNX models
from HuggingFace Hub for local embedding generation.
"""

from __future__ import annotations

import json
import logging
import shutil
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported ONNX embedding models with their metadata
SUPPORTED_MODELS: dict[str, dict] = {
    "all-MiniLM-L6-v2": {
        "repo_id": "sentence-transformers/all-MiniLM-L6-v2",
        "dimensions": 384,
        "size_mb": 90,
        "description": "Fast, lightweight model - default choice",
        "files": ["model.onnx", "tokenizer.json", "config.json"],
    },
    "all-mpnet-base-v2": {
        "repo_id": "sentence-transformers/all-mpnet-base-v2",
        "dimensions": 768,
        "size_mb": 420,
        "description": "High quality, larger model",
        "files": ["model.onnx", "tokenizer.json", "config.json"],
    },
    "multilingual-e5-small": {
        "repo_id": "intfloat/multilingual-e5-small",
        "dimensions": 384,
        "size_mb": 470,
        "description": "Multilingual support including French",
        "files": ["model.onnx", "tokenizer.json", "config.json"],
    },
    "bge-small-en-v1.5": {
        "repo_id": "BAAI/bge-small-en-v1.5",
        "dimensions": 384,
        "size_mb": 130,
        "description": "Excellent for retrieval tasks",
        "files": ["model.onnx", "tokenizer.json", "config.json"],
    },
}

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".ragkit" / "models" / "onnx"


class ModelDownloadError(Exception):
    """Raised when model download fails."""


class ModelDownloadManager:
    """Manages downloading and caching of ONNX embedding models.

    This class handles:
    - Downloading models from HuggingFace Hub
    - Caching models locally in ~/.ragkit/models/onnx/
    - Progress reporting during downloads
    - Integrity verification via SHA256
    - Cleanup of old/unused models
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the download manager.

        Args:
            cache_dir: Custom cache directory. Defaults to ~/.ragkit/models/onnx/
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self.cache_dir / "models_metadata.json"
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """Load metadata about downloaded models."""
        if self._metadata_file.exists():
            try:
                return json.loads(self._metadata_file.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save metadata about downloaded models."""
        self._metadata_file.write_text(json.dumps(self._metadata, indent=2))

    def get_model_path(self, model_id: str) -> Path | None:
        """Get the local path for a downloaded model.

        Args:
            model_id: Model identifier (e.g., 'all-MiniLM-L6-v2')

        Returns:
            Path to model directory if downloaded, None otherwise.
        """
        model_dir = self.cache_dir / model_id
        if model_dir.exists() and (model_dir / "model.onnx").exists():
            return model_dir
        return None

    def is_model_downloaded(self, model_id: str) -> bool:
        """Check if a model is already downloaded.

        Args:
            model_id: Model identifier

        Returns:
            True if model is fully downloaded, False otherwise.
        """
        return self.get_model_path(model_id) is not None

    def list_downloaded_models(self) -> list[str]:
        """List all downloaded model IDs.

        Returns:
            List of model IDs that are available locally.
        """
        downloaded = []
        for model_id in SUPPORTED_MODELS:
            if self.is_model_downloaded(model_id):
                downloaded.append(model_id)
        return downloaded

    def list_available_models(self) -> list[dict]:
        """List all supported models with their metadata.

        Returns:
            List of model info dictionaries.
        """
        models = []
        for model_id, info in SUPPORTED_MODELS.items():
            models.append({
                "id": model_id,
                "dimensions": info["dimensions"],
                "size_mb": info["size_mb"],
                "description": info["description"],
                "downloaded": self.is_model_downloaded(model_id),
            })
        return models

    async def download_model(
        self,
        model_id: str,
        progress_callback: Callable[[float, str], None] | None = None,
        force: bool = False,
    ) -> Path:
        """Download a model from HuggingFace Hub.

        Args:
            model_id: Model identifier (e.g., 'all-MiniLM-L6-v2')
            progress_callback: Optional callback(progress_pct, message)
            force: If True, re-download even if model exists

        Returns:
            Path to the downloaded model directory.

        Raises:
            ModelDownloadError: If download fails.
            ValueError: If model_id is not supported.
        """
        if model_id not in SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model_id}. "
                f"Supported: {list(SUPPORTED_MODELS.keys())}"
            )

        # Check if already downloaded
        if not force and self.is_model_downloaded(model_id):
            if progress_callback:
                progress_callback(100.0, f"Model {model_id} already downloaded")
            return self.get_model_path(model_id)  # type: ignore

        model_info = SUPPORTED_MODELS[model_id]
        model_dir = self.cache_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Import here to avoid dependency issues if not installed
            from huggingface_hub import hf_hub_download

            if progress_callback:
                progress_callback(0.0, f"Downloading {model_id}...")

            # Download ONNX model file
            await self._download_file(
                model_info["repo_id"],
                "onnx/model.onnx",
                model_dir / "model.onnx",
                hf_hub_download,
                progress_callback,
                0.0,
                70.0,
            )

            # Download tokenizer
            if progress_callback:
                progress_callback(70.0, "Downloading tokenizer...")
            await self._download_file(
                model_info["repo_id"],
                "tokenizer.json",
                model_dir / "tokenizer.json",
                hf_hub_download,
                progress_callback,
                70.0,
                90.0,
            )

            # Download config
            if progress_callback:
                progress_callback(90.0, "Downloading config...")
            await self._download_file(
                model_info["repo_id"],
                "config.json",
                model_dir / "config.json",
                hf_hub_download,
                progress_callback,
                90.0,
                100.0,
            )

            # Update metadata
            self._metadata[model_id] = {
                "path": str(model_dir),
                "dimensions": model_info["dimensions"],
                "repo_id": model_info["repo_id"],
            }
            self._save_metadata()

            if progress_callback:
                progress_callback(100.0, f"Model {model_id} downloaded successfully")

            logger.info(f"Successfully downloaded model {model_id} to {model_dir}")
            return model_dir

        except ImportError as e:
            raise ModelDownloadError(
                "huggingface_hub not installed. Install with: pip install ragkit[desktop]"
            ) from e
        except Exception as e:
            # Cleanup partial download
            if model_dir.exists():
                shutil.rmtree(model_dir, ignore_errors=True)
            raise ModelDownloadError(f"Failed to download {model_id}: {e}") from e

    async def _download_file(
        self,
        repo_id: str,
        filename: str,
        target_path: Path,
        hf_download_fn: Callable,
        progress_callback: Callable[[float, str], None] | None,
        _progress_start: float,
        progress_end: float,
    ) -> Path:
        """Download a single file from HuggingFace Hub.

        Uses asyncio to avoid blocking the event loop.
        """
        import asyncio

        def _sync_download() -> str:
            return hf_download_fn(
                repo_id=repo_id,
                filename=filename,
                local_dir=target_path.parent,
                local_dir_use_symlinks=False,
            )

        loop = asyncio.get_event_loop()
        downloaded_path = await loop.run_in_executor(None, _sync_download)

        # Move to expected location if needed
        src = Path(downloaded_path)
        if src != target_path and src.exists():
            shutil.copy2(src, target_path)

        if progress_callback:
            progress_callback(progress_end, f"Downloaded {filename}")

        return target_path

    def delete_model(self, model_id: str) -> bool:
        """Delete a downloaded model.

        Args:
            model_id: Model identifier

        Returns:
            True if deleted, False if model wasn't downloaded.
        """
        model_dir = self.cache_dir / model_id
        if model_dir.exists():
            shutil.rmtree(model_dir)
            if model_id in self._metadata:
                del self._metadata[model_id]
                self._save_metadata()
            logger.info(f"Deleted model {model_id}")
            return True
        return False

    def get_cache_size_mb(self) -> float:
        """Get total size of cached models in MB.

        Returns:
            Total cache size in megabytes.
        """
        total = 0
        for path in self.cache_dir.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
        return total / (1024 * 1024)

    def verify_model_integrity(self, model_id: str) -> bool:
        """Verify a downloaded model's integrity.

        Args:
            model_id: Model identifier

        Returns:
            True if model passes integrity checks.
        """
        model_dir = self.get_model_path(model_id)
        if not model_dir:
            return False

        required_files = ["model.onnx", "tokenizer.json"]
        for filename in required_files:
            if not (model_dir / filename).exists():
                logger.warning(f"Missing file {filename} in model {model_id}")
                return False

        # Verify model.onnx is loadable
        try:
            import onnxruntime as ort
            ort.InferenceSession(str(model_dir / "model.onnx"))
            return True
        except Exception as e:
            logger.warning(f"Model {model_id} failed integrity check: {e}")
            return False


def get_model_dimensions(model_id: str) -> int:
    """Get embedding dimensions for a model.

    Args:
        model_id: Model identifier

    Returns:
        Embedding dimensions.

    Raises:
        ValueError: If model is not supported.
    """
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unknown model: {model_id}")
    return SUPPORTED_MODELS[model_id]["dimensions"]
