from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from phantomnet_core.contracts import CONTRACT_VERSION, DetectionRule, EventEnvelope


def test_event_envelope_normalizes_naive_timestamps_to_utc():
    event = EventEnvelope(
        tenant_id="tenant-lab",
        source="honeypot",
        event_type="auth_attempt",
        timestamp=datetime(2026, 1, 1, 0, 0, 0),
        payload={"source_ip": "198.51.100.42"},
    )
    assert event.schema_version == CONTRACT_VERSION
    assert event.timestamp.tzinfo == timezone.utc


def test_event_envelope_fingerprint_is_deterministic():
    event = EventEnvelope(
        tenant_id="tenant-lab",
        source="agent",
        event_type="process_event",
        payload={"pid": 42, "name": "safe-test"},
    )
    assert event.payload_fingerprint() == event.payload_fingerprint()


def test_detection_rule_requires_versioned_and_bounded_definition():
    rule = DetectionRule(
        rule_id="RULE-BRUTEFORCE-001",
        version="1.0.0",
        name="Repeated authentication failures",
        description="Detects a bounded number of failed authentication attempts.",
        event_types=["auth_attempt"],
        threshold=5,
        window_seconds=300,
        expected_outcome={"severity": "high", "action": "create_ticket"},
    )
    assert rule.threshold == 5
    assert rule.enabled is True

    with pytest.raises(ValidationError):
        DetectionRule(
            rule_id="RULE-BAD",
            version="one",
            name="Bad rule",
            description="Missing semantic version",
        )
