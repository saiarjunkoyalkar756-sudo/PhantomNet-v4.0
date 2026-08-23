"""Controlled end-to-end SOC workflow validation and lightweight canonical pipeline benchmark.

All adapters are simulated; this test sends no external traffic and performs no endpoint or firewall action.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from statistics import median

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.audit_log_collector.integrity import verify_chain
from backend_api.bas_engine.baseline_scenarios import emit_baseline_events
from backend_api.case_management_service.workflow import CaseWorkflow
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.endpoint_inventory_service.forwarders import WazuhForwarderService
from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest, EventEnvelope, WazuhTelemetryBatch


TENANT_ID = "00000000-0000-0000-0000-000000000001"


class SimulatedContainmentAdapter:
    """Records in-process calls only; no command, network, or endpoint operation is performed."""

    name = "e2e-simulated-containment"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute(self, request, approval):
        self.calls.append("execute")
        return {
            "enforced": True,
            "verified": True,
            "rollback_available": True,
            "detail": "Simulation-only isolation verification.",
            "simulation": True,
        }

    def rollback(self, request, approval):
        self.calls.append("rollback")
        return {
            "enforced": False,
            "verified": True,
            "detail": "Simulation-only release verification.",
            "simulation": True,
        }


@dataclass
class SocHarness:
    engine: object
    sessions: object
    processor: CanonicalBrokerProcessor
    alert_workflow: AlertWorkflow
    case_workflow: CaseWorkflow
    forwarders: WazuhForwarderService
    endpoint_repository: EndpointInventoryRepository
    containment: GovernedContainmentService
    containment_adapter: SimulatedContainmentAdapter
    audit_signing_key: str
    audit_key_id: str


async def _harness() -> SocHarness:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    detection_repository = DetectionRepository(sessions)
    alert_workflow = AlertWorkflow(sessions)
    processor = CanonicalBrokerProcessor(detection_repository, alert_workflow=alert_workflow)
    endpoint_repository = EndpointInventoryRepository(sessions)
    endpoint_ingestion = EndpointTelemetryIngestion(endpoint_repository)
    forwarders = WazuhForwarderService(sessions, endpoint_ingestion)
    containment_adapter = SimulatedContainmentAdapter()
    audit_signing_key = secrets.token_urlsafe(32)
    audit_key_id = "e2e-sandbox-key"
    containment = GovernedContainmentService(
        sessions,
        containment_adapter,
        audit_signing_key=audit_signing_key,
        audit_key_id=audit_key_id,
    )
    return SocHarness(engine, sessions, processor, alert_workflow, CaseWorkflow(sessions), forwarders, endpoint_repository, containment, containment_adapter, audit_signing_key, audit_key_id)


def _wazuh_alert():
    return {
        "id": "e2e-wazuh-alert-001",
        "timestamp": "2026-08-18T18:00:00Z",
        "agent": {"id": "e2e-agent-001", "name": "e2e-lab-host", "ip": "10.0.0.50", "os": {"name": "Ubuntu", "version": "24.04"}},
        "rule": {"id": "550", "level": 10, "description": "File integrity changed", "groups": ["syscheck", "integrity"]},
        "syscheck": {"event": "modified", "path": "/tmp/phantomnet-e2e.txt", "sha256_before": "before", "sha256_after": "after"},
    }


@pytest.mark.asyncio
async def test_controlled_end_to_end_soc_workflow_covers_detection_to_containment_governance():
    harness = await _harness()
    try:
        raw_bas_events = emit_baseline_events(TENANT_ID, "e2e-baseline-correlation")
        broker_results = []
        for event in raw_bas_events:
            normalized = normalize_event(event.model_dump(mode="json"))
            broker_results.append(await harness.processor.process(normalized))

        assert sum(len(result.created_detection_ids) for result in broker_results) == 10
        assert sum(len(result.alert_workflows) for result in broker_results) == 10
        alerts = await harness.alert_workflow.list_for_tenant(TENANT_ID)
        assert len(alerts) == 10
        assert all(alert.mitre_evidence for alert in alerts)

        case, case_created = await harness.case_workflow.create_from_alert(TENANT_ID, alerts[0].alert_id, "e2e-analyst")
        playbook = await harness.case_workflow.request_playbook(
            TENANT_ID, case.case_id, "endpoint-isolation-playbook", "1.0.0", "e2e-analyst", requires_approval=True
        )
        approved_playbook = await harness.case_workflow.transition_playbook(TENANT_ID, playbook.run_id, "approved", "e2e-approver")
        running_playbook = await harness.case_workflow.transition_playbook(TENANT_ID, approved_playbook.run_id, "running", "e2e-analyst")
        completed_playbook = await harness.case_workflow.transition_playbook(TENANT_ID, running_playbook.run_id, "completed", "e2e-analyst")
        assert case_created is True
        assert completed_playbook.status == "completed"
        assert completed_playbook.evidence["execution_dispatched"] is False
        tenant_cases = await harness.case_workflow.list_cases(TENANT_ID)
        assert [tenant_case.case_id for tenant_case in tenant_cases] == [case.case_id]

        forwarder, token = await harness.forwarders.register(TENANT_ID, "e2e-wazuh-forwarder", "e2e-admin")
        streamed = await harness.forwarders.stream_batch(
            forwarder.forwarder_id,
            token,
            WazuhTelemetryBatch(batch_id="e2e-wazuh-batch-0001", sequence=1, alerts=[_wazuh_alert()]),
        )
        assert streamed["asset_created"] == 1
        assert streamed["integrity_created"] == 1
        assert streamed["automatic_enforcement"] is False

        assets = await harness.endpoint_repository.list_assets(TENANT_ID)
        assert len(assets) == 1
        containment_request, created = await harness.containment.request(
            ContainmentRequest(
                tenant_id=TENANT_ID,
                action="isolate_endpoint",
                target=assets[0].hostname,
                asset_id=assets[0].asset_id,
                playbook_id=completed_playbook.playbook_id,
                requested_by="e2e-analyst",
                idempotency_key="e2e-governed-containment-0001",
                parameters={"simulation": True},
                requires_approval=True,
                automatic_enforcement=False,
            )
        )
        approval = await harness.containment.approve(
            ContainmentApproval(
                request_id=containment_request.request_id,
                tenant_id=TENANT_ID,
                decision="approved",
                decided_by="e2e-approver",
                reason="Controlled end-to-end simulation approval.",
            )
        )
        execution = await harness.containment.execute(TENANT_ID, containment_request.request_id, "e2e-approver")
        rollback = await harness.containment.rollback(TENANT_ID, containment_request.request_id, "e2e-approver")
        assert created is True
        assert approval.decision == "approved"
        assert execution.status == "verified"
        assert rollback.status == "rolled_back"
        assert harness.containment_adapter.calls == ["execute", "rollback"]

        async with harness.sessions() as session:
            audit_rows = list(
                await session.scalars(
                    select(ContainmentAuditRecordRow)
                    .where(ContainmentAuditRecordRow.tenant_id == TENANT_ID)
                    .order_by(ContainmentAuditRecordRow.id)
                )
            )
        audit_records = [
            {
                "record_id": row.record_id,
                "timestamp": row.timestamp,
                "actor_id": row.actor_id,
                "action": row.action,
                "payload": row.payload,
                "previous_hash": row.previous_hash,
                "record_hash": row.record_hash,
                "signature": row.signature,
                "signature_key_id": row.signature_key_id,
            }
            for row in audit_rows
        ]
        assert verify_chain(audit_records, signing_key=harness.audit_signing_key, require_signature=True, expected_key_id=harness.audit_key_id)
    finally:
        await harness.engine.dispose()


@pytest.mark.asyncio
async def test_controlled_canonical_pipeline_benchmark_reports_reproducible_latency_shape():
    """Benchmark only in-memory SQLite processing; it is not a production capacity claim."""
    harness = await _harness()
    event_count = 60
    timings_ms: list[float] = []
    try:
        for index in range(event_count):
            event = EventEnvelope(
                tenant_id=TENANT_ID,
                source="bas-engine",
                event_type="auth_attempt",
                severity="high",
                payload={"scenario_id": "BAS-AUTH-001", "source_ip": "198.51.100.42", "failed_attempts": 5, "sample": index},
                correlation_id=f"benchmark-{index}",
                tags=["bas", "controlled", "non-destructive"],
                provenance={"execution": "telemetry-fixture"},
            )
            started = time.perf_counter()
            result = await harness.processor.process(normalize_event(event.model_dump(mode="json")))
            timings_ms.append((time.perf_counter() - started) * 1000)
            assert len(result.created_detection_ids) == 1
        ordered = sorted(timings_ms)
        p95 = ordered[int(len(ordered) * 0.95) - 1]
        assert len(timings_ms) == event_count
        assert median(timings_ms) >= 0
        assert p95 >= 0
        # Prevent accidental pathological regressions in this deterministic in-memory harness.
        assert p95 < 1000
    finally:
        await harness.engine.dispose()
