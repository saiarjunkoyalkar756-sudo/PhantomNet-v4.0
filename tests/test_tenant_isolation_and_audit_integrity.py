from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.audit_log_collector.verification import ContainmentAuditVerifier
from backend_api.case_management_service.workflow import CaseWorkflow
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.governed_correlation import GovernedCorrelationRepository
from backend_api.correlation_engine.telemetry_replication import (
    TelemetryReplicationRepository,
    TelemetryReplicationService,
)
from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.response_automation import ResponseAutomationPolicyRepository
from phantomnet_core.contracts import (
    ContainmentApproval,
    ContainmentRequest,
    DetectionRecord,
    GovernedCorrelationRule,
    ResponseAutomationPolicy,
    TelemetryReplicationTarget,
    EventEnvelope,
)


TENANT_A = "00000000-0000-0000-0000-000000000001"
TENANT_B = "00000000-0000-0000-0000-000000000002"
AUDIT_KEY = "tenant-isolation-audit-key"


class VerifiedAdapter:
    name = "tenant-isolation-verifier"

    def execute(self, request, approval):
        return {"enforced": True, "verified": True, "rollback_available": True}

    def rollback(self, request, approval):
        return {"enforced": False, "verified": True}


class RecordingTransport:
    async def deliver(self, target, event):
        return None


async def _sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False), engine


def _detection(tenant_id: str, suffix: str) -> DetectionRecord:
    return DetectionRecord(
        detection_id=f"isolation-detection-{suffix}",
        tenant_id=tenant_id,
        event_id=f"isolation-event-{suffix}",
        rule_id="isolation-governed-rule",
        rule_version="1.0.0",
        severity="high",
        title=f"Isolation detection {suffix}",
        evidence={"asset_id": f"asset-{suffix}"},
    )


def _correlation_rule(tenant_id: str, suffix: str) -> GovernedCorrelationRule:
    return GovernedCorrelationRule(
        tenant_id=tenant_id,
        version="1.0.0",
        name=f"Isolation rule {suffix}",
        description="Tenant isolation verification fixture.",
        event_types=["process.start"],
        predicates=[{"field": "payload.hostname", "operator": "equals", "value": f"host-{suffix}"}],
        severity="high",
        mitre_techniques=["T1059"],
        mitre_tactics=["execution"],
        threshold=1,
        window_seconds=60,
    )


def _policy(tenant_id: str, suffix: str) -> ResponseAutomationPolicy:
    return ResponseAutomationPolicy(
        tenant_id=tenant_id,
        name=f"Isolation proposal policy {suffix}",
        trigger_rule_ids=["isolation-governed-rule"],
        minimum_severity="high",
        action="block_indicator",
        target="203.0.113.42",
    )


def _event(tenant_id: str, suffix: str) -> EventEnvelope:
    return EventEnvelope(
        event_id=f"replication-isolation-{suffix}",
        tenant_id=tenant_id,
        source="test-agent",
        event_type="process.start",
        payload={"hostname": f"host-{suffix}"},
    )


@pytest.mark.asyncio
async def test_cross_tenant_read_and_lookup_boundaries_hold_across_governed_evidence_stores():
    sessions, engine = await _sessions()
    try:
        detections = DetectionRepository(sessions)
        alerts = AlertWorkflow(sessions)
        cases = CaseWorkflow(sessions)
        correlation = GovernedCorrelationRepository(sessions)
        policies = ResponseAutomationPolicyRepository(sessions)
        replication = TelemetryReplicationRepository(sessions)

        detection_a, _ = await detections.persist(_detection(TENANT_A, "a"))
        detection_b, _ = await detections.persist(_detection(TENANT_B, "b"))
        alert_a = await alerts.ingest_detection(detection_a)
        alert_b = await alerts.ingest_detection(detection_b)
        case_a, _ = await cases.create_from_alert(TENANT_A, alert_a.alert.alert_id, "analyst-a")
        case_b, _ = await cases.create_from_alert(TENANT_B, alert_b.alert.alert_id, "analyst-b")

        await correlation.upsert(_correlation_rule(TENANT_A, "a"))
        await correlation.upsert(_correlation_rule(TENANT_B, "b"))
        await policies.upsert(_policy(TENANT_A, "a"))
        await policies.upsert(_policy(TENANT_B, "b"))
        target_a = await replication.upsert_target(
            TelemetryReplicationTarget(tenant_id=TENANT_A, target_region="eu-west-1", stream_name="tenant-a.telemetry")
        )
        await replication.upsert_target(
            TelemetryReplicationTarget(tenant_id=TENANT_B, target_region="ap-south-1", stream_name="tenant-b.telemetry")
        )
        await TelemetryReplicationService(replication, RecordingTransport(), source_region="us-east-1").replicate_event(_event(TENANT_A, "a"))

        assert [record.detection_id for record in await detections.list_for_tenant(TENANT_A)] == [detection_a.detection_id]
        assert [record.alert_id for record in await alerts.list_for_tenant(TENANT_A)] == [alert_a.alert.alert_id]
        assert (await cases.get_case(TENANT_A, case_a.case_id)).case_id == case_a.case_id
        with pytest.raises(LookupError, match="authenticated tenant"):
            await cases.get_case(TENANT_A, case_b.case_id)
        with pytest.raises(LookupError, match="authenticated tenant"):
            await cases.create_from_alert(TENANT_A, alert_b.alert.alert_id, "analyst-a")

        assert [rule.tenant_id for rule in await correlation.list_rules(TENANT_A)] == [TENANT_A]
        assert [policy.tenant_id for policy in await policies.list_for_tenant(TENANT_A)] == [TENANT_A]
        assert [target.target_id for target in await replication.list_targets(TENANT_A)] == [target_a.target_id]
        receipts_a = await replication.list_receipts(TENANT_A)
        assert len(receipts_a) == 1 and receipts_a[0].tenant_id == TENANT_A
        assert await replication.list_receipts(TENANT_B) == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_audit_chains_verify_independently_reject_orm_mutation_and_detect_raw_tampering():
    sessions, engine = await _sessions()
    try:
        service = GovernedContainmentService(
            sessions,
            adapter=VerifiedAdapter(),
            audit_signing_key=AUDIT_KEY,
            audit_key_id="isolation-key",
        )
        request = ContainmentRequest(
            tenant_id=TENANT_A,
            action="isolate_endpoint",
            target="asset-a",
            asset_id="asset-a",
            requested_by="analyst-a",
            idempotency_key="audit-isolation-a",
            requires_approval=True,
            automatic_enforcement=False,
        )
        stored, _ = await service.request(request)
        await service.approve(
            ContainmentApproval(
                request_id=stored.request_id,
                tenant_id=TENANT_A,
                decision="approved",
                decided_by="admin-a",
                reason="Isolation verification fixture.",
            )
        )
        await service.execute(TENANT_A, stored.request_id, "admin-a")
        await service.rollback(TENANT_A, stored.request_id, "admin-a")

        other, _ = await service.request(
            ContainmentRequest(
                tenant_id=TENANT_B,
                action="isolate_endpoint",
                target="asset-b",
                asset_id="asset-b",
                requested_by="analyst-b",
                idempotency_key="audit-isolation-b",
                requires_approval=True,
                automatic_enforcement=False,
            )
        )
        verifier = ContainmentAuditVerifier(sessions)
        verified_a = await verifier.verify_tenant(TENANT_A, signing_key=AUDIT_KEY, expected_key_id="isolation-key")
        verified_b = await verifier.verify_tenant(TENANT_B, signing_key=AUDIT_KEY, expected_key_id="isolation-key")
        assert verified_a.valid is True and verified_a.record_count == 4
        assert verified_b.valid is True and verified_b.record_count == 1
        assert (await verifier.verify_tenant(TENANT_A, signing_key="wrong-key", expected_key_id="isolation-key")).valid is False

        async with sessions() as session:
            row = await session.scalar(select(ContainmentAuditRecordRow).where(ContainmentAuditRecordRow.tenant_id == TENANT_A))
            row.payload = {"tamper": "orm"}
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()
            await session.rollback()

        assert (await verifier.verify_tenant(TENANT_A, signing_key=AUDIT_KEY, expected_key_id="isolation-key")).valid is True
        async with sessions() as session:
            row = await session.scalar(select(ContainmentAuditRecordRow).where(ContainmentAuditRecordRow.tenant_id == TENANT_A))
            await session.delete(row)
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()
            await session.rollback()

        assert (await verifier.verify_tenant(TENANT_A, signing_key=AUDIT_KEY, expected_key_id="isolation-key")).valid is True
        async with sessions() as session:
            await session.execute(
                update(ContainmentAuditRecordRow)
                .where(ContainmentAuditRecordRow.tenant_id == TENANT_A)
                .values(payload={"tamper": "raw-sql"})
            )
            await session.commit()
        assert (await verifier.verify_tenant(TENANT_A, signing_key=AUDIT_KEY, expected_key_id="isolation-key")).valid is False
        assert (await verifier.verify_tenant(TENANT_B, signing_key=AUDIT_KEY, expected_key_id="isolation-key")).valid is True
        assert other.tenant_id == TENANT_B
    finally:
        await engine.dispose()


def test_governed_containment_exposes_auditor_only_read_only_verification_route():
    from backend_api.soar_engine.governed_api import router

    routes = [route for route in router.routes if route.path == "/governed-containment/audit/verify"]
    assert len(routes) == 1
    assert routes[0].methods == {"GET"}
