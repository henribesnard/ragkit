"""Tests for PII detection and redaction."""

import pytest

from ragkit.config.schema_v2 import SecurityConfigV2
from ragkit.security.exceptions import PIIDetectedException
from ragkit.security.pii_detector import PIIDetector


def test_pii_email_redaction():
    config = SecurityConfigV2(pii_detection_mode="redact")
    detector = PIIDetector(config)

    text = "Contact john.doe@example.com or call 555-123-4567"
    redacted, entities = detector.detect_and_redact(text)

    assert "[EMAIL_ADDRESS]" in redacted
    assert "[PHONE_NUMBER]" in redacted
    assert "john.doe@example.com" not in redacted
    assert entities


def test_pii_block_mode():
    config = SecurityConfigV2(pii_detection_mode="block")
    detector = PIIDetector(config)

    with pytest.raises(PIIDetectedException):
        detector.detect_and_redact("My SSN is 123-45-6789")
