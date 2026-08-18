from backend_api.event_normalizer.main import normalize_event
from phantomnet_core.contracts import CONTRACT_VERSION


def test_normalizer_emits_canonical_versioned_envelope(monkeypatch):
    monkeypatch.setattr(
        "backend_api.event_normalizer.main.dna_engine.tag_event",
        lambda event: {**event, "dna_tag": "test-only"},
    )

    normalized = normalize_event(
        {
            "tenant_id": "00000000-0000-0000-0000-000000000002",
            "source": "honeypot",
            "event_type": "auth_attempt",
            "severity": "high",
            "payload": {"source_ip": "198.51.100.42", "username": "test"},
            "correlation_id": "corr-001",
        }
    )

    assert normalized["schema_version"] == CONTRACT_VERSION
    assert normalized["platform_schema_version"] == CONTRACT_VERSION
    assert normalized["event_id"]
    assert normalized["timestamp"].endswith("Z") or "+00:00" in normalized["timestamp"]
    assert normalized["payload"]["source_ip"] == "198.51.100.42"
    assert normalized["provenance"]["normalizer"] == "event-normalizer"
    assert normalized["dna_tag"] == "test-only"
