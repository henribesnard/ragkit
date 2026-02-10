"""Tests for audit logging."""

from ragkit.config.schema_v2 import SecurityConfigV2
from ragkit.security.audit_logger import AuditLogger


def test_audit_logger_writes_entry(tmp_path):
    config = SecurityConfigV2(audit_logging_enabled=True, log_all_queries=True)
    db_path = tmp_path / "audit_logs.db"
    logger = AuditLogger(config, db_path=db_path)

    logger.log_query(
        user_id="user-1",
        query="How to secure API endpoints?",
        response="Use authentication headers.",
        documents_accessed=["doc-1"],
        metadata={"latency_ms": 120.5, "cost_usd": 0.01},
        pii_detected=[],
        toxicity_score=0.0,
    )

    entries = logger.list_entries(limit=10)
    assert len(entries) == 1
    assert entries[0]["query_hash"]
