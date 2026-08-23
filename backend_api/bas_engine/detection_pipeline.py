"""Deterministic detection validation for controlled BAS baseline telemetry.

This adapter is intentionally restricted to the five non-destructive BAS scenarios. It
normalizes each canonical event first, emits a versioned detection record only when the
expected defensive condition is present, and never initiates response or containment.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Dict, List

from backend_api.bas_engine.baseline_scenarios import emit_baseline_events
from phantomnet_core.contracts import DetectionRecord, DetectionRule, EventEnvelope, MitreEvidence


BAS_DETECTION_RULES: Dict[str, DetectionRule] = {
    "BAS-AUTH-001": DetectionRule(
        rule_id="bas.auth.repeated-failures",
        version="1.0.0",
        name="BAS repeated authentication failures",
        description="Detects the controlled five-failure authentication scenario.",
        event_types=["auth_attempt"],
        severity="high",
        threshold=5,
        conditions={"failed_attempts_gte": 5},
        mitre_techniques=["T1110"],
        mitre_tactics=["credential-access"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-PROC-001": DetectionRule(
        rule_id="bas.process.unexpected-lineage",
        version="1.0.0",
        name="BAS unexpected process lineage",
        description="Detects the controlled unexpected-child process lineage scenario.",
        event_types=["process_event"],
        severity="medium",
        conditions={"process_name": "unexpected-child", "parent": "test-parent"},
        mitre_techniques=["T1059"],
        mitre_tactics=["execution"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-DNS-001": DetectionRule(
        rule_id="bas.dns.high-entropy-query",
        version="1.0.0",
        name="BAS high-entropy DNS query",
        description="Detects the controlled high-entropy DNS query scenario.",
        event_types=["dns_query"],
        severity="medium",
        conditions={"entropy_gte": 3.5, "query_suffix": ".example.test"},
        mitre_techniques=["T1071.004"],
        mitre_tactics=["command-and-control"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-NET-001": DetectionRule(
        rule_id="bas.network.unexpected-outbound",
        version="1.0.0",
        name="BAS unexpected outbound connection",
        description="Detects the controlled outbound documentation-network scenario.",
        event_types=["network_connection"],
        severity="high",
        conditions={"destination_ip": "203.0.113.42", "destination_port": 443},
        mitre_techniques=["T1071.001"],
        mitre_tactics=["command-and-control"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-FILE-001": DetectionRule(
        rule_id="bas.file.sensitive-modification",
        version="1.0.0",
        name="BAS sensitive file modification",
        description="Detects the controlled sensitive file write scenario.",
        event_types=["file_event"],
        severity="high",
        conditions={"path": "/tmp/phantomnet-lab-sensitive.txt", "operation": "write"},
        mitre_techniques=["T1565.001"],
        mitre_tactics=["impact"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-SCHED-001": DetectionRule(
        rule_id="bas.execution.controlled-scheduled-task",
        version="1.0.0",
        name="BAS controlled scheduled-task metadata",
        description="Detects only the named documentation-only scheduled-task telemetry fixture.",
        event_types=["scheduled_task_event"],
        severity="medium",
        conditions={"task_name": "phantomnet-lab-maintenance", "command_reference": "documentation-only"},
        mitre_techniques=["T1053.005"],
        mitre_tactics=["execution"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-RDP-001": DetectionRule(
        rule_id="bas.lateral-movement.controlled-rdp-failures",
        version="1.0.0",
        name="BAS repeated controlled RDP authentication failures",
        description="Detects only the documentation-range controlled RDP failure fixture.",
        event_types=["remote_service_auth"],
        severity="high",
        conditions={"protocol": "RDP", "failed_attempts_gte": 3, "source_ip": "198.51.100.43"},
        mitre_techniques=["T1021.001"],
        mitre_tactics=["lateral-movement"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
    "BAS-DISC-001": DetectionRule(
        rule_id="bas.discovery.controlled-lab-tree",
        version="1.0.0",
        name="BAS controlled lab-tree discovery volume",
        description="Detects only the bounded lab-tree inventory telemetry fixture.",
        event_types=["file_inventory_event"],
        severity="medium",
        conditions={"root": "/tmp/phantomnet-lab-tree", "discovered_entries_gte": 100},
        mitre_techniques=["T1083"],
        mitre_tactics=["discovery"],
        expected_outcome={"detection": True, "automatic_enforcement": False},
    ),
}


def _has_required_safety_metadata(event: EventEnvelope) -> bool:
    return (
        event.source == "bas-engine"
        and {"bas", "controlled", "non-destructive"}.issubset(event.tags)
        and event.provenance.get("execution") == "telemetry-fixture"
    )


def _auth_matches(payload: Mapping[str, Any]) -> bool:
    return int(payload.get("failed_attempts", 0)) >= 5


def _process_matches(payload: Mapping[str, Any]) -> bool:
    return payload.get("process_name") == "unexpected-child" and payload.get("parent") == "test-parent"


def _dns_matches(payload: Mapping[str, Any]) -> bool:
    return float(payload.get("entropy", 0)) >= 3.5 and str(payload.get("query", "")).endswith(".example.test")


def _network_matches(payload: Mapping[str, Any]) -> bool:
    return payload.get("destination_ip") == "203.0.113.42" and payload.get("destination_port") == 443


def _file_matches(payload: Mapping[str, Any]) -> bool:
    return payload.get("path") == "/tmp/phantomnet-lab-sensitive.txt" and payload.get("operation") == "write"


def _scheduled_task_matches(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("task_name") == "phantomnet-lab-maintenance"
        and payload.get("command_reference") == "documentation-only"
    )


def _rdp_matches(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("protocol") == "RDP"
        and payload.get("source_ip") == "198.51.100.43"
        and int(payload.get("failed_attempts", 0)) >= 3
    )


def _discovery_matches(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("root") == "/tmp/phantomnet-lab-tree"
        and payload.get("collection_mode") == "telemetry-fixture"
        and int(payload.get("discovered_entries", 0)) >= 100
    )


SCENARIO_MATCHERS: Dict[str, Callable[[Mapping[str, Any]], bool]] = {
    "BAS-AUTH-001": _auth_matches,
    "BAS-PROC-001": _process_matches,
    "BAS-DNS-001": _dns_matches,
    "BAS-NET-001": _network_matches,
    "BAS-FILE-001": _file_matches,
    "BAS-SCHED-001": _scheduled_task_matches,
    "BAS-RDP-001": _rdp_matches,
    "BAS-DISC-001": _discovery_matches,
}


def evaluate_normalized_baseline_event(normalized_event: Mapping[str, Any]) -> DetectionRecord | None:
    """Return one controlled BAS detection for a normalized canonical event, if matched."""
    event = EventEnvelope.model_validate(normalized_event)
    scenario_id = event.payload.get("scenario_id")
    if not isinstance(scenario_id, str) or not _has_required_safety_metadata(event):
        return None

    rule = BAS_DETECTION_RULES.get(scenario_id)
    matcher = SCENARIO_MATCHERS.get(scenario_id)
    if rule is None or matcher is None or event.event_type not in rule.event_types or not matcher(event.payload):
        return None

    mitre_evidence = [
        MitreEvidence(
            technique_id=technique_id,
            tactic=rule.mitre_tactics[index] if index < len(rule.mitre_tactics) else "unknown",
            confidence=1.0,
            rationale="Governed BAS rule mapping validated against the scenario condition.",
            evidence_fields=sorted(rule.conditions.keys()),
        )
        for index, technique_id in enumerate(rule.mitre_techniques)
    ]

    return DetectionRecord(
        detection_id=f"bas-{event.event_id}-{rule.rule_id}",
        rule_id=rule.rule_id,
        rule_version=rule.version,
        event_id=event.event_id,
        tenant_id=event.tenant_id,
        correlation_id=event.correlation_id,
        severity=rule.severity,
        title=rule.name,
        evidence={
            "scenario_id": scenario_id,
            "event_type": event.event_type,
            "payload_fingerprint": event.payload_fingerprint(),
            "normalized_at": normalized_event.get("normalized_at"),
            "rule_conditions": rule.conditions,
            "mitre_techniques": rule.mitre_techniques,
            "mitre_tactics": rule.mitre_tactics,
        },
        mitre_evidence=mitre_evidence,
        tags=["bas", "controlled", "non-destructive", "detection-validation"],
        automatic_enforcement=False,
    )


def run_baseline_detection(tenant_id: str, correlation_id: str) -> List[DetectionRecord]:
    """Normalize all BAS telemetry fixtures and return their matching detection records.

    Importing the normalizer at execution time keeps this deterministic helper free of
    broker or service-startup side effects. It does not publish events or trigger response.
    """
    from backend_api.event_normalizer.main import normalize_event

    detections: List[DetectionRecord] = []
    for event in emit_baseline_events(tenant_id=tenant_id, correlation_id=correlation_id):
        normalized_event = normalize_event(event.model_dump(mode="json"))
        detection = evaluate_normalized_baseline_event(normalized_event)
        if detection is not None:
            detections.append(detection)
    return detections
