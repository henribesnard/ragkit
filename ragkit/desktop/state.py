"""Application state management for RAGKIT Desktop.

This module manages the global state of the desktop application,
including database connections, embedding models, and managers.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ragkit.agents import AgentOrchestrator
from ragkit.config.defaults import default_agents_config, default_retrieval_config
from ragkit.config.schema import EmbeddingModelConfig, EmbeddingParams, LLMConfig, LLMModelConfig, LLMParams
from ragkit.embedding import create_embedder
from ragkit.embedding.base import BaseEmbedder
from ragkit.llm import LLMRouter
from ragkit.llm.providers.ollama_manager import OllamaManager
from ragkit.retrieval import RetrievalEngine
from ragkit.security.keyring import SecureKeyStore
from ragkit.storage.conversation_manager import ConversationManager
from ragkit.storage.kb_manager import KnowledgeBaseManager
from ragkit.storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# Default data directory
DEFAULT_DATA_DIR = Path.home() / ".ragkit"


class AppState:
    """Global application state container.

    Manages:
    - SQLite database connection
    - Knowledge base manager
    - Conversation manager
    - Secure key storage
    - Application settings
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize app state.

        Args:
            data_dir: Base directory for application data
        """
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Components (initialized in initialize())
        self.db: SQLiteStore | None = None
        self.kb_manager: KnowledgeBaseManager | None = None
        self.conversation_manager: ConversationManager | None = None
        self.key_store: SecureKeyStore | None = None
        self.ollama_manager: OllamaManager | None = None

        # Settings cache
        self._settings: dict = {}

        # Caches
        self._embedder_cache: dict[tuple[str, str, str, int | None], BaseEmbedder] = {}
        self._llm_router_cache: dict[tuple[str, str, str], LLMRouter] = {}
        self._orchestrator_cache: dict[str, AgentOrchestrator] = {}

    async def initialize(self) -> None:
        """Initialize all components."""
        logger.info(f"Initializing app state with data dir: {self.data_dir}")

        # Initialize SQLite store
        db_path = self.data_dir / "ragkit.db"
        self.db = SQLiteStore(db_path=db_path)

        # Initialize managers
        vectors_path = self.data_dir / "vectors"
        self.kb_manager = KnowledgeBaseManager(
            db=self.db,
            vectors_path=vectors_path,
        )

        self.conversation_manager = ConversationManager(db=self.db)

        # Initialize key store
        self.key_store = SecureKeyStore(db=self.db)

        # Initialize Ollama manager
        self.ollama_manager = OllamaManager()

        # Load settings
        self._load_settings()

        logger.info("App state initialized successfully")

    async def shutdown(self) -> None:
        """Clean up resources."""
        logger.info("Shutting down app state")
        # Components will be garbage collected

    def _load_settings(self) -> None:
        """Load settings from database."""
        if not self.db:
            return

        self._settings = {
            "embedding_provider": self.db.get_setting("embedding_provider", "onnx_local"),
            "embedding_model": self.db.get_setting("embedding_model", "all-MiniLM-L6-v2"),
            "llm_provider": self.db.get_setting("llm_provider", "ollama"),
            "llm_model": self.db.get_setting("llm_model", "llama3.2:3b"),
            "theme": self.db.get_setting("theme", "system"),
        }

    def get_settings(self) -> dict:
        """Get current settings."""
        return self._settings.copy()

    def update_settings(self, settings: dict) -> dict:
        """Update settings.

        Args:
            settings: Dictionary of settings to update

        Returns:
            Updated settings dictionary
        """
        if not self.db:
            return self._settings

        for key, value in settings.items():
            if key in self._settings:
                self.db.set_setting(key, value)
                self._settings[key] = value

        # Clear caches when settings change
        self._embedder_cache.clear()
        self._llm_router_cache.clear()
        self._orchestrator_cache.clear()

        return self._settings.copy()

    def _get_api_key(self, provider: str) -> str | None:
        if not self.key_store:
            return None
        return self.key_store.retrieve(provider)

    def get_embedder(self, model: str, dimensions: int | None = None) -> BaseEmbedder:
        provider = self._settings.get("embedding_provider", "onnx_local")
        api_key = self._get_api_key(provider) or ""
        cache_key = (provider, model, api_key, dimensions)
        cached = self._embedder_cache.get(cache_key)
        if cached:
            return cached

        config = EmbeddingModelConfig(
            provider=provider,
            model=model,
            api_key=api_key or None,
            params=EmbeddingParams(dimensions=dimensions),
        )
        embedder = create_embedder(config)
        self._embedder_cache[cache_key] = embedder
        return embedder

    def get_llm_router(self) -> LLMRouter:
        provider = self._settings.get("llm_provider", "ollama")
        model = self._settings.get("llm_model", "llama3.2:3b")
        api_key = self._get_api_key(provider) or ""
        cache_key = (provider, model, api_key)
        cached = self._llm_router_cache.get(cache_key)
        if cached:
            return cached

        primary = LLMModelConfig(
            provider=provider,
            model=model,
            api_key=api_key or None,
            params=LLMParams(temperature=0.7, max_tokens=800, top_p=0.95),
            timeout=60,
            max_retries=2,
        )
        fast = LLMModelConfig(
            provider=provider,
            model=model,
            api_key=api_key or None,
            params=LLMParams(temperature=0.3, max_tokens=300, top_p=0.9),
        )
        config = LLMConfig(primary=primary, fast=fast)
        router = LLMRouter(config)
        self._llm_router_cache[cache_key] = router
        return router

    async def get_orchestrator(self, kb_id: str) -> AgentOrchestrator:
        cached = self._orchestrator_cache.get(kb_id)
        if cached:
            return cached
        if not self.kb_manager:
            raise RuntimeError("KnowledgeBaseManager not initialized")
        kb = await self.kb_manager.get(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base not found: {kb_id}")

        embedder = self.get_embedder(kb.embedding_model, kb.embedding_dimensions)
        vector_store = self.kb_manager.get_vector_store(kb_id)
        retrieval = RetrievalEngine(default_retrieval_config(), vector_store, embedder)
        orchestrator = AgentOrchestrator(
            default_agents_config(),
            retrieval,
            self.get_llm_router(),
            metrics_enabled=False,
        )
        self._orchestrator_cache[kb_id] = orchestrator
        return orchestrator
