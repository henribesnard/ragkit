"""Application state management for RAGKIT Desktop.

This module manages the global state of the desktop application,
including database connections, embedding models, and managers.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ragkit.llm.providers.ollama_manager import OllamaManager
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

        return self._settings.copy()
