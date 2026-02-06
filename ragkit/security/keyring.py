"""Secure API key storage for RAGKIT Desktop.

This module provides secure storage for API keys using:
1. OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
2. Fallback to Fernet encryption with local key file

The goal is to never store API keys in plain text.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragkit.storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# Service name for keychain storage
KEYCHAIN_SERVICE = "ragkit-desktop"

# Local encryption key file path
DEFAULT_KEY_FILE = Path.home() / ".ragkit" / ".encryption_key"


class SecureKeyStore:
    """Secure storage for API keys.

    Uses OS keychain when available, with fallback to encrypted local storage.

    Supported backends:
    - macOS: Keychain
    - Windows: Credential Manager
    - Linux: Secret Service (GNOME Keyring, KWallet)
    - Fallback: Fernet encryption with local key file
    """

    def __init__(
        self,
        db: SQLiteStore | None = None,
        key_file: Path | None = None,
    ) -> None:
        """Initialize secure key store.

        Args:
            db: Optional SQLite store for encrypted key storage fallback
            key_file: Optional path to encryption key file
        """
        self.db = db
        self.key_file = key_file or DEFAULT_KEY_FILE
        self._keyring_available: bool | None = None
        self._fernet_key: bytes | None = None

    @property
    def keyring_available(self) -> bool:
        """Check if OS keyring is available."""
        if self._keyring_available is None:
            self._keyring_available = self._check_keyring()
        return self._keyring_available

    def _check_keyring(self) -> bool:
        """Check if keyring module is available and working."""
        try:
            import keyring
            from keyring.errors import NoKeyringError

            # Try a test operation
            try:
                keyring.get_keyring()
                return True
            except NoKeyringError:
                logger.warning("No keyring backend available")
                return False
        except ImportError:
            logger.warning("keyring module not installed")
            return False

    def _get_fernet(self) -> Any:  # Returns cryptography.fernet.Fernet
        """Get or create Fernet instance for encryption."""
        from cryptography.fernet import Fernet

        if self._fernet_key is None:
            self._fernet_key = self._load_or_create_key()

        return Fernet(self._fernet_key)

    def _load_or_create_key(self) -> bytes:
        """Load encryption key from file or create new one."""
        from cryptography.fernet import Fernet

        self.key_file.parent.mkdir(parents=True, exist_ok=True)

        if self.key_file.exists():
            key = self.key_file.read_bytes()
            logger.debug("Loaded encryption key from file")
        else:
            key = Fernet.generate_key()
            # Create file with restrictive permissions
            self.key_file.write_bytes(key)
            try:
                # Set file permissions to owner-only (Unix)
                os.chmod(self.key_file, 0o600)
            except (OSError, AttributeError):
                # Windows doesn't support chmod the same way
                pass
            logger.info(f"Created new encryption key at {self.key_file}")

        return key

    def store(self, provider: str, api_key: str) -> None:
        """Store an API key securely.

        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            api_key: The API key to store
        """
        if self.keyring_available:
            self._store_keyring(provider, api_key)
        else:
            self._store_encrypted(provider, api_key)

        logger.info(f"Stored API key for provider: {provider}")

    def _store_keyring(self, provider: str, api_key: str) -> None:
        """Store key in OS keychain."""
        import keyring

        keyring.set_password(KEYCHAIN_SERVICE, provider, api_key)

    def _store_encrypted(self, provider: str, api_key: str) -> None:
        """Store key with Fernet encryption in SQLite."""
        if self.db is None:
            raise RuntimeError(
                "SQLite database required for encrypted storage. "
                "Either install keyring or provide db parameter."
            )

        fernet = self._get_fernet()
        encrypted = fernet.encrypt(api_key.encode()).decode()
        self.db.store_api_key(provider, encrypted)

    def retrieve(self, provider: str) -> str | None:
        """Retrieve an API key.

        Args:
            provider: Provider name

        Returns:
            API key string, or None if not found.
        """
        if self.keyring_available:
            return self._retrieve_keyring(provider)
        else:
            return self._retrieve_encrypted(provider)

    def _retrieve_keyring(self, provider: str) -> str | None:
        """Retrieve key from OS keychain."""
        import keyring

        return keyring.get_password(KEYCHAIN_SERVICE, provider)

    def _retrieve_encrypted(self, provider: str) -> str | None:
        """Retrieve and decrypt key from SQLite."""
        if self.db is None:
            return None

        encrypted = self.db.get_api_key(provider)
        if encrypted is None:
            return None

        try:
            fernet = self._get_fernet()
            decrypted = fernet.decrypt(encrypted.encode()).decode()
            return decrypted
        except Exception as e:
            logger.error(f"Failed to decrypt API key for {provider}: {e}")
            return None

    def delete(self, provider: str) -> bool:
        """Delete an API key.

        Args:
            provider: Provider name

        Returns:
            True if deleted, False if not found.
        """
        if self.keyring_available:
            return self._delete_keyring(provider)
        else:
            return self._delete_encrypted(provider)

    def _delete_keyring(self, provider: str) -> bool:
        """Delete key from OS keychain."""
        import keyring
        from keyring.errors import PasswordDeleteError

        try:
            keyring.delete_password(KEYCHAIN_SERVICE, provider)
            logger.info(f"Deleted API key for provider: {provider}")
            return True
        except PasswordDeleteError:
            return False

    def _delete_encrypted(self, provider: str) -> bool:
        """Delete key from SQLite."""
        if self.db is None:
            return False
        return self.db.delete_api_key(provider)

    def list_providers(self) -> list[str]:
        """List all providers with stored API keys.

        Returns:
            List of provider names.
        """
        if self.keyring_available:
            # Keyring doesn't have a built-in list function
            # We need to track this in SQLite regardless
            if self.db:
                return self.db.list_api_key_providers()
            return []
        else:
            if self.db:
                return self.db.list_api_key_providers()
            return []

    def has_key(self, provider: str) -> bool:
        """Check if a key exists for a provider.

        Args:
            provider: Provider name

        Returns:
            True if key exists.
        """
        return self.retrieve(provider) is not None

    def test_key(self, provider: str, api_key: str) -> bool:
        """Test if an API key is valid (basic format check).

        Args:
            provider: Provider name
            api_key: API key to test

        Returns:
            True if key appears valid.
        """
        if not api_key or len(api_key) < 10:
            return False

        # Provider-specific format checks
        if provider == "openai":
            return api_key.startswith("sk-") and len(api_key) > 20
        elif provider == "anthropic":
            return api_key.startswith("sk-ant-") and len(api_key) > 20
        elif provider == "cohere":
            return len(api_key) > 20

        # Default: basic length check
        return len(api_key) >= 20

    def get_storage_backend(self) -> str:
        """Get the current storage backend being used.

        Returns:
            Backend name ('keyring' or 'encrypted_sqlite').
        """
        if self.keyring_available:
            import keyring

            backend = keyring.get_keyring()
            return f"keyring ({type(backend).__name__})"
        return "encrypted_sqlite"


def mask_api_key(api_key: str) -> str:
    """Mask an API key for display.

    Args:
        api_key: Full API key

    Returns:
        Masked key showing only first and last 4 characters.

    Example:
        sk-abc123...xyz789
    """
    if len(api_key) <= 8:
        return "****"

    return f"{api_key[:7]}...{api_key[-4:]}"
