"""Custom exception hierarchy for RAGKIT."""


class RAGKitError(Exception):
    """Base exception for RAGKIT."""


class ConfigError(RAGKitError):
    """Raised when configuration is invalid or cannot be loaded."""


class IngestionError(RAGKitError):
    """Raised during ingestion pipeline failures."""


class EmbeddingError(RAGKitError):
    """Raised when embedding generation fails."""


class RetrievalError(RAGKitError):
    """Raised during retrieval failures."""


class LLMError(RAGKitError):
    """Raised when LLM calls fail."""


class AgentError(RAGKitError):
    """Raised for agent orchestration failures."""
