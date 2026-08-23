"""Safe BAS baseline scenarios for controlled detection-pipeline validation.

These are telemetry fixtures, not exploit implementations. Each emits an event describing
an observable defensive condition against documentation-only test assets.
"""

from __future__ import annotations

from typing import Any, Dict, List

from phantomnet_core.contracts import EventEnvelope


BASELINE_SCENARIOS: List[Dict[str, Any]] = [
    {
        "scenario_id": "BAS-AUTH-001",
        "name": "Repeated authentication failures",
        "event_type": "auth_attempt",
        "severity": "high",
        "payload": {"source_ip": "198.51.100.42", "failed_attempts": 5, "username": "lab-user"},
    },
    {
        "scenario_id": "BAS-PROC-001",
        "name": "Unexpected process lineage",
        "event_type": "process_event",
        "severity": "medium",
        "payload": {"host": "lab-endpoint-01", "process_name": "unexpected-child", "parent": "test-parent"},
    },
    {
        "scenario_id": "BAS-DNS-001",
        "name": "High-entropy DNS query",
        "event_type": "dns_query",
        "severity": "medium",
        "payload": {"host": "lab-endpoint-01", "query": "a8f3k7m2q9.example.test", "entropy": 3.8},
    },
    {
        "scenario_id": "BAS-NET-001",
        "name": "Unexpected outbound connection",
        "event_type": "network_connection",
        "severity": "high",
        "payload": {"source_host": "lab-endpoint-01", "destination_ip": "203.0.113.42", "destination_port": 443},
    },
    {
        "scenario_id": "BAS-FILE-001",
        "name": "Sensitive file modification",
        "event_type": "file_event",
        "severity": "high",
        "payload": {"host": "lab-endpoint-01", "path": "/tmp/phantomnet-lab-sensitive.txt", "operation": "write"},
    },
    {
        "scenario_id": "BAS-SCHED-001",
        "name": "Controlled scheduled-task metadata",
        "event_type": "scheduled_task_event",
        "severity": "medium",
        "payload": {
            "host": "lab-endpoint-01",
            "task_name": "phantomnet-lab-maintenance",
            "created_by": "lab-user",
            "command_reference": "documentation-only",
        },
    },
    {
        "scenario_id": "BAS-RDP-001",
        "name": "Repeated controlled RDP authentication failures",
        "event_type": "remote_service_auth",
        "severity": "high",
        "payload": {
            "host": "lab-endpoint-01",
            "protocol": "RDP",
            "source_ip": "198.51.100.43",
            "failed_attempts": 3,
        },
    },
    {
        "scenario_id": "BAS-DISC-001",
        "name": "Controlled lab-tree discovery volume",
        "event_type": "file_inventory_event",
        "severity": "medium",
        "payload": {
            "host": "lab-endpoint-01",
            "root": "/tmp/phantomnet-lab-tree",
            "discovered_entries": 100,
            "collection_mode": "telemetry-fixture",
        },
    },
    {
        "scenario_id": "BAS-WMI-001",
        "name": "Controlled WMI activity metadata",
        "event_type": "wmi_activity",
        "severity": "medium",
        "payload": {
            "host": "lab-endpoint-01",
            "namespace": "root/cimv2",
            "method": "InventoryQuery",
            "execution": "telemetry-fixture",
        },
    },
    {
        "scenario_id": "BAS-CRED-001",
        "name": "Controlled credential-artifact alert metadata",
        "event_type": "credential_access_alert",
        "severity": "high",
        "payload": {
            "host": "lab-endpoint-01",
            "target": "lab-credential-artifact",
            "detector": "fixture-only",
            "access_mode": "metadata",
        },
    },
]


def emit_baseline_events(tenant_id: str, correlation_id: str) -> List[EventEnvelope]:
    """Create versioned events for each safe baseline scenario."""
    return [
        EventEnvelope(
            tenant_id=tenant_id,
            source="bas-engine",
            event_type=scenario["event_type"],
            severity=scenario["severity"],
            payload={"scenario_id": scenario["scenario_id"], **scenario["payload"]},
            correlation_id=correlation_id,
            tags=["bas", "controlled", "non-destructive"],
            provenance={"scenario": scenario["name"], "execution": "telemetry-fixture"},
        )
        for scenario in BASELINE_SCENARIOS
    ]
