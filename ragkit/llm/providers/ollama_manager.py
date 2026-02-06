"""Ollama Manager for local LLM management.

This module provides utilities for managing Ollama installations,
including model discovery, downloading, and health checking.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)

# Default Ollama API endpoint
DEFAULT_OLLAMA_HOST = "http://localhost:11434"

# Recommended models for RAGKIT
RECOMMENDED_MODELS = {
    "llama3.2:3b": {
        "name": "Llama 3.2 3B",
        "size": "2.0 GB",
        "description": "Fast and efficient, good for most tasks",
        "quality": "good",
        "speed": "fast",
    },
    "llama3.1:8b": {
        "name": "Llama 3.1 8B",
        "size": "4.7 GB",
        "description": "High quality responses, requires good GPU",
        "quality": "excellent",
        "speed": "medium",
    },
    "mistral:7b": {
        "name": "Mistral 7B",
        "size": "4.1 GB",
        "description": "Excellent for reasoning tasks",
        "quality": "excellent",
        "speed": "medium",
    },
    "phi3:mini": {
        "name": "Phi-3 Mini",
        "size": "2.2 GB",
        "description": "Small but capable model",
        "quality": "good",
        "speed": "very_fast",
    },
    "qwen2.5:3b": {
        "name": "Qwen 2.5 3B",
        "size": "1.9 GB",
        "description": "Good multilingual support",
        "quality": "good",
        "speed": "fast",
    },
}

# Embedding models for Ollama
EMBEDDING_MODELS = {
    "nomic-embed-text": {
        "name": "Nomic Embed Text",
        "size": "274 MB",
        "dimensions": 768,
        "description": "High quality text embeddings",
    },
    "mxbai-embed-large": {
        "name": "MixedBread Embed Large",
        "size": "670 MB",
        "dimensions": 1024,
        "description": "Large embedding model for better accuracy",
    },
    "all-minilm": {
        "name": "All-MiniLM",
        "size": "45 MB",
        "dimensions": 384,
        "description": "Small and fast embedding model",
    },
}


@dataclass
class OllamaModel:
    """Represents an Ollama model."""

    name: str
    size: int  # Size in bytes
    digest: str
    modified_at: str
    details: dict[str, Any] | None = None


@dataclass
class OllamaStatus:
    """Ollama service status."""

    installed: bool
    running: bool
    version: str | None = None
    error: str | None = None


@dataclass
class PullProgress:
    """Model pull progress information."""

    status: str
    total: int
    completed: int
    percent: float


class OllamaManager:
    """Manager for Ollama LLM service.

    Provides methods to:
    - Check if Ollama is installed and running
    - List available and installed models
    - Pull new models with progress tracking
    - Delete models
    - Get model information
    """

    def __init__(self, host: str = DEFAULT_OLLAMA_HOST):
        """Initialize the Ollama manager.

        Args:
            host: Ollama API host URL
        """
        self.host = host.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.host,
                timeout=httpx.Timeout(30.0, connect=5.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # Installation & Status
    # =========================================================================

    def is_installed(self) -> bool:
        """Check if Ollama is installed on the system.

        Returns:
            True if Ollama binary is found in PATH
        """
        return shutil.which("ollama") is not None

    def get_install_path(self) -> Path | None:
        """Get the path to the Ollama binary.

        Returns:
            Path to ollama binary or None if not found
        """
        path = shutil.which("ollama")
        return Path(path) if path else None

    async def is_running(self) -> bool:
        """Check if Ollama service is running.

        Returns:
            True if Ollama API is responding
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
        except Exception as e:
            logger.warning(f"Error checking Ollama status: {e}")
            return False

    async def get_version(self) -> str | None:
        """Get Ollama version.

        Returns:
            Version string or None if unavailable
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/version")
            if response.status_code == 200:
                data = response.json()
                return data.get("version")
        except Exception as e:
            logger.warning(f"Error getting Ollama version: {e}")
        return None

    async def get_status(self) -> OllamaStatus:
        """Get comprehensive Ollama status.

        Returns:
            OllamaStatus with installation and running info
        """
        installed = self.is_installed()

        if not installed:
            return OllamaStatus(
                installed=False,
                running=False,
                error="Ollama is not installed",
            )

        running = await self.is_running()
        version = await self.get_version() if running else None

        return OllamaStatus(
            installed=True,
            running=running,
            version=version,
            error=None if running else "Ollama service is not running",
        )

    # =========================================================================
    # Model Management
    # =========================================================================

    async def list_models(self) -> list[OllamaModel]:
        """List all installed models.

        Returns:
            List of installed OllamaModel objects
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/tags")

            if response.status_code != 200:
                logger.error(f"Failed to list models: {response.status_code}")
                return []

            data = response.json()
            models = []

            for model_data in data.get("models", []):
                model = OllamaModel(
                    name=model_data.get("name", ""),
                    size=model_data.get("size", 0),
                    digest=model_data.get("digest", ""),
                    modified_at=model_data.get("modified_at", ""),
                    details=model_data.get("details"),
                )
                models.append(model)

            return models

        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> dict[str, Any] | None:
        """Get detailed information about a model.

        Args:
            model_name: Name of the model

        Returns:
            Model information dict or None if not found
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/show",
                json={"name": model_name},
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.error(f"Error getting model info: {e}")

        return None

    async def has_model(self, model_name: str) -> bool:
        """Check if a model is installed.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is installed
        """
        models = await self.list_models()
        # Normalize model names for comparison
        model_base = model_name.split(":")[0]
        for model in models:
            if model.name == model_name or model.name.startswith(f"{model_base}:"):
                return True
        return False

    async def pull_model(
        self,
        model_name: str,
        progress_callback: Callable[[PullProgress], None] | None = None,
    ) -> bool:
        """Pull (download) a model from Ollama registry.

        Args:
            model_name: Name of the model to pull
            progress_callback: Optional callback for progress updates

        Returns:
            True if successful
        """
        try:
            client = await self._get_client()

            # Use streaming to get progress updates
            async with client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name},
                timeout=httpx.Timeout(None, connect=10.0),  # No read timeout for long downloads
            ) as response:
                if response.status_code != 200:
                    logger.error(f"Failed to pull model: {response.status_code}")
                    return False

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        import json

                        data = json.loads(line)

                        status = data.get("status", "")
                        total = data.get("total", 0)
                        completed = data.get("completed", 0)

                        percent = 0.0
                        if total > 0:
                            percent = (completed / total) * 100

                        if progress_callback:
                            progress = PullProgress(
                                status=status,
                                total=total,
                                completed=completed,
                                percent=percent,
                            )
                            progress_callback(progress)

                        # Check for completion
                        if status == "success":
                            return True

                    except Exception as e:
                        logger.debug(f"Error parsing progress: {e}")
                        continue

            return True

        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model.

        Args:
            model_name: Name of the model to delete

        Returns:
            True if successful
        """
        try:
            client = await self._get_client()
            response = await client.request(
                "DELETE",
                "/api/delete",
                json={"name": model_name},
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            return False

    # =========================================================================
    # Service Control
    # =========================================================================

    async def start_service(self) -> bool:
        """Attempt to start the Ollama service.

        Returns:
            True if service started successfully
        """
        if not self.is_installed():
            logger.error("Cannot start: Ollama is not installed")
            return False

        if await self.is_running():
            return True

        try:
            # Try to start ollama serve in background
            if sys.platform == "win32":
                subprocess.Popen(
                    ["ollama", "serve"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )

            # Wait for service to start
            for _ in range(10):
                await asyncio.sleep(1)
                if await self.is_running():
                    return True

            logger.warning("Ollama service did not start in time")
            return False

        except Exception as e:
            logger.error(f"Error starting Ollama service: {e}")
            return False

    # =========================================================================
    # Utilities
    # =========================================================================

    def get_recommended_models(self) -> dict[str, dict[str, Any]]:
        """Get list of recommended models for RAGKIT.

        Returns:
            Dict of model name to model info
        """
        return RECOMMENDED_MODELS

    def get_embedding_models(self) -> dict[str, dict[str, Any]]:
        """Get list of available embedding models.

        Returns:
            Dict of model name to model info
        """
        return EMBEDDING_MODELS

    @staticmethod
    def get_install_instructions() -> dict[str, str]:
        """Get installation instructions for each platform.

        Returns:
            Dict of platform to installation instructions
        """
        return {
            "darwin": "Install with Homebrew: brew install ollama\n"
            "Or download from: https://ollama.ai/download/mac",
            "linux": "curl -fsSL https://ollama.ai/install.sh | sh",
            "win32": "Download from: https://ollama.ai/download/windows",
        }

    def format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human readable size string
        """
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# Singleton instance
_manager: OllamaManager | None = None


def get_ollama_manager(host: str = DEFAULT_OLLAMA_HOST) -> OllamaManager:
    """Get the singleton OllamaManager instance.

    Args:
        host: Ollama API host URL

    Returns:
        OllamaManager instance
    """
    global _manager
    if _manager is None:
        _manager = OllamaManager(host)
    return _manager
