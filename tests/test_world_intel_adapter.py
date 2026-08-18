from backend_api.threat_intelligence_service.world_intel_adapter import WorldIntelEnricher, correlate_evidence


def test_world_intel_enrichment_preserves_read_only_provenance():
    calls = []

    def transport(tool_name, arguments):
        calls.append((tool_name, arguments))
        return {"sources": [{"url": "https://example.test/intel"}], "summary": "Context only"}

    enrichment = WorldIntelEnricher(transport=transport).enrich("198.51.100.42")
    assert enrichment["status"] == "success"
    assert calls == [("lookup_indicator_context", {"indicator": "198.51.100.42"})]
    assert enrichment["evidence"]["provenance"]["read_only"] is True
    assert enrichment["evidence"]["provenance"]["automation"] == "prohibited"


def test_world_intel_correlation_never_requests_automatic_enforcement():
    correlation = correlate_evidence(
        {"event_id": "evt-001", "correlation_id": "corr-001"},
        {"evidence": {"provider": "world-intel-mcp"}},
    )
    assert correlation["response_recommendation"] == "human_review_required"
    assert correlation["automatic_enforcement"] is False


def test_unconfigured_or_unallowlisted_world_intel_requests_do_not_call_external_services():
    unavailable = WorldIntelEnricher().enrich("198.51.100.42")
    assert unavailable["status"] == "unavailable"

    denied = WorldIntelEnricher(transport=lambda *_: {}).enrich("198.51.100.42", tool_name="write_report")
    assert denied["status"] == "failure"
