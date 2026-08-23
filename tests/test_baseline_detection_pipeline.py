from backend_api.bas_engine.baseline_scenarios import emit_baseline_events
from backend_api.bas_engine.detection_pipeline import evaluate_normalized_baseline_event, run_baseline_detection
from backend_api.event_normalizer.main import normalize_event
from phantomnet_core.contracts import CONTRACT_VERSION


TENANT_ID = "00000000-0000-0000-0000-000000000001"
CORRELATION_ID = "corr-baseline-pipeline-001"


def test_all_safe_baseline_scenarios_normalize_into_detections():
    detections = run_baseline_detection(TENANT_ID, CORRELATION_ID)

    assert len(detections) == 10
    assert {detection.evidence["scenario_id"] for detection in detections} == {
        "BAS-AUTH-001",
        "BAS-PROC-001",
        "BAS-DNS-001",
        "BAS-NET-001",
        "BAS-FILE-001",
        "BAS-SCHED-001",
        "BAS-RDP-001",
        "BAS-DISC-001",
        "BAS-WMI-001",
        "BAS-CRED-001",
    }
    technique_by_scenario = {
        detection.evidence["scenario_id"]: detection.mitre_evidence[0].technique_id
        for detection in detections
    }
    assert technique_by_scenario == {
        "BAS-AUTH-001": "T1110",
        "BAS-PROC-001": "T1059",
        "BAS-DNS-001": "T1071.004",
        "BAS-NET-001": "T1071.001",
        "BAS-FILE-001": "T1565.001",
        "BAS-SCHED-001": "T1053.005",
        "BAS-RDP-001": "T1021.001",
        "BAS-DISC-001": "T1083",
        "BAS-WMI-001": "T1047",
        "BAS-CRED-001": "T1003",
    }
    for detection in detections:
        assert detection.schema_version == CONTRACT_VERSION
        assert detection.tenant_id == TENANT_ID
        assert detection.correlation_id == CORRELATION_ID
        assert detection.status == "detected"
        assert detection.automatic_enforcement is False
        assert {"bas", "controlled", "non-destructive", "detection-validation"}.issubset(detection.tags)
        assert detection.evidence["normalized_at"]


def test_normalization_preserves_bas_safety_provenance_for_detection():
    event = emit_baseline_events(TENANT_ID, CORRELATION_ID)[0]
    normalized = normalize_event(event.model_dump(mode="json"))
    detection = evaluate_normalized_baseline_event(normalized)

    assert normalized["provenance"]["execution"] == "telemetry-fixture"
    assert normalized["provenance"]["normalizer"] == "event-normalizer"
    assert detection is not None
    assert detection.evidence["scenario_id"] == "BAS-AUTH-001"


def test_bas_adapter_rejects_events_without_required_safety_metadata_or_conditions():
    event = emit_baseline_events(TENANT_ID, CORRELATION_ID)[0]
    normalized = normalize_event(event.model_dump(mode="json"))

    unsafe_copy = {**normalized, "tags": ["bas"]}
    assert evaluate_normalized_baseline_event(unsafe_copy) is None

    altered_copy = {**normalized, "payload": {**normalized["payload"], "failed_attempts": 4}}
    assert evaluate_normalized_baseline_event(altered_copy) is None


def test_new_bas_scenarios_refuse_altered_non_destructive_fixture_conditions():
    events = {event.payload["scenario_id"]: event for event in emit_baseline_events(TENANT_ID, CORRELATION_ID)}
    expected_rejections = {
        "BAS-SCHED-001": {"task_name": "unapproved-task"},
        "BAS-RDP-001": {"failed_attempts": 2},
        "BAS-DISC-001": {"discovered_entries": 99},
        "BAS-WMI-001": {"method": "UnapprovedMethod"},
        "BAS-CRED-001": {"access_mode": "unapproved"},
    }

    for scenario_id, altered_fields in expected_rejections.items():
        normalized = normalize_event(events[scenario_id].model_dump(mode="json"))
        altered = {**normalized, "payload": {**normalized["payload"], **altered_fields}}
        assert evaluate_normalized_baseline_event(altered) is None
