"""Security-related exceptions."""

from __future__ import annotations

from ragkit.exceptions import RAGKitError


class SecurityError(RAGKitError):
    """Base class for security and compliance errors."""


class PIIDetectedException(SecurityError):
    """Raised when PII is detected and policy is set to block."""


class ToxicContentException(SecurityError):
    """Raised when toxic content exceeds the configured threshold."""


class PromptInjectionException(SecurityError):
    """Raised when prompt injection patterns are detected."""


class RateLimitExceededException(SecurityError):
    """Raised when rate limits are exceeded."""


class AuditLogError(SecurityError):
    """Raised when audit logging fails."""
