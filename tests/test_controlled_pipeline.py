from backend_api.event_normalizer.main import normalize_event
from backend_api.soar_engine.response_providers import HttpResponseProvider, ResponseRequest
from backend_api.threat_intelligence_service.world_intel_adapter import WorldIntelEnricher, correlate_evidence
from phantomnet_core.contracts import DetectionRule


def test_controlled_telemetry_to_decision_pipeline(monkeypatch):
    monkeypatch.setattr(
        "backend_api.event_normalizer.main.dna_engine.tag_event",
        lambda event: {**event, "dna_tag": "controlled-test"},
    )
    raw = {
        "tenant_id": "00000000-0000-0000-0000-000000000002",
        "source": "honeypot",
        "event_type": "auth_attempt",
        "severity": "high",
        "payload": {"source_ip": "198.51.100.42", "failed_attempts": 5},
        "correlation_id": "corr-controlled-001",
    }
    event = normalize_event(raw)

    rule = DetectionRule(
        rule_id="RULE-BRUTEFORCE-001",
        version="1.0.0",
        name="Repeated authentication failures",
        description="Detects five failed attempts within a bounded window.",
        event_types=["auth_attempt"],
        threshold=5,
        expected_outcome={"response": "human_review_required"},
    )
    assert event["event_type"] in rule.event_types
    assert event["payload"]["failed_attempts"] >= rule.threshold

    enrichment = WorldIntelEnricher(
        transport=lambda tool, args: {"indicator": args["indicator"], "classification": "test-context"}
    ).enrich(event["payload"]["source_ip"])
    correlation = correlate_evidence(event, enrichment)
    assert correlation["automatic_enforcement"] is False

    # An external containment request without configured provider credentials is an
    # intentional refusal, not a false claim of enforcement.
    response = HttpResponseProvider(
        endpoint="",
        api_token="",
        allowed_tenants={event["tenant_id"]},
        allowed_targets={event["payload"]["source_ip"]},
    ).execute(
        ResponseRequest(
            action="block_ip",
            target=event["payload"]["source_ip"],
            tenant_id=event["tenant_id"],
            requested_by="analyst@example.test",
            approval_id="APR-CONTROLLED-001",
            idempotency_key="corr-controlled-001:block-ip",
            metadata={"requester_role": "analyst", "correlation_id": event["correlation_id"]},
        )
    )
    assert response["enforced"] is False
    assert response["verified"] is False
