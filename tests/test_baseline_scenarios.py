from backend_api.bas_engine.baseline_scenarios import BASELINE_SCENARIOS, emit_baseline_events
from phantomnet_core.contracts import CONTRACT_VERSION


def test_eight_baseline_scenarios_emit_safe_canonical_events():
    events = emit_baseline_events("tenant-lab", "corr-baseline-001")

    assert len(BASELINE_SCENARIOS) == 8
    assert len(events) == 8
    assert {event.payload["scenario_id"] for event in events} == {
        "BAS-AUTH-001",
        "BAS-PROC-001",
        "BAS-DNS-001",
        "BAS-NET-001",
        "BAS-FILE-001",
        "BAS-SCHED-001",
        "BAS-RDP-001",
        "BAS-DISC-001",
    }
    for event in events:
        assert event.schema_version == CONTRACT_VERSION
        assert event.correlation_id == "corr-baseline-001"
        assert "non-destructive" in event.tags
        assert event.provenance["execution"] == "telemetry-fixture"
