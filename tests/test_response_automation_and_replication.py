from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.correlation_engine.telemetry_replication import (
    DisabledTelemetryReplicationTransport,
    KafkaTelemetryReplicationTransport,
    TelemetryReplicationRepository,
    TelemetryReplicationService,
    configured_telemetry_replication_transport,
)
from backend_api.shared.database import Base, ContainmentExecutionRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.response_automation import (
    GovernedResponseProposalService,
    ResponseAutomationPolicyRepository,
    ResponseProposalObserver,
)
from phantomnet_core.contracts import (
    DetectionRecord,
    EventEnvelope,
    ResponseAutomationPolicy,
    TelemetryReplicationTarget,
)


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


async def _sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False), engine


def _policy(tenant_id: str = TENANT_ID, minimum_severity: str = "high") -> ResponseAutomationPolicy:
    return ResponseAutomationPolicy(
        tenant_id=tenant_id,
        name="Block approved lab indicator after governed detection",
        trigger_rule_ids=["governed-rule-1"],
        minimum_severity=minimum_severity,
        action="block_indicator",
        target="203.0.113.42",
        parameters={"security_group_id": "sg-0123456789abcdef0", "rule_id": "sgr-0123456789abcdef0"},
    )


def _detection(severity: str = "high", tenant_id: str = TENANT_ID) -> DetectionRecord:
    return DetectionRecord(
        detection_id="detection-response-automation-1",
        rule_id="governed-rule-1",
        rule_version="1.0.0",
        event_id="event-response-automation-1",
        tenant_id=tenant_id,
        severity=severity,
        title="Governed high confidence detection",
        evidence={"payload_fingerprint": "test"},
    )


def _event(tenant_id: str = TENANT_ID) -> EventEnvelope:
    return EventEnvelope(
        event_id="event-replication-1",
        tenant_id=tenant_id,
        source="endpoint-agent",
        event_type="process.start",
        payload={"hostname": "app-01", "process": "admin-tool"},
    )


def _target(tenant_id: str = TENANT_ID, region: str = "eu-west-1") -> TelemetryReplicationTarget:
    return TelemetryReplicationTarget(
        tenant_id=tenant_id,
        target_region=region,
        stream_name="phantomnet.telemetry.replica",
    )


def test_replication_transport_is_disabled_without_explicit_broker_configuration(monkeypatch):
    monkeypatch.delenv("PHANTOMNET_TELEMETRY_REPLICATION_ENABLED", raising=False)
    monkeypatch.delenv("PHANTOMNET_REPLICATION_KAFKA_BOOTSTRAP_SERVERS", raising=False)
    assert isinstance(configured_telemetry_replication_transport(), DisabledTelemetryReplicationTransport)

    monkeypatch.setenv("PHANTOMNET_TELEMETRY_REPLICATION_ENABLED", "true")
    assert isinstance(configured_telemetry_replication_transport(), DisabledTelemetryReplicationTransport)

    monkeypatch.setenv("PHANTOMNET_REPLICATION_KAFKA_BOOTSTRAP_SERVERS", "replica-broker.example.test:9093")
    assert isinstance(configured_telemetry_replication_transport(), KafkaTelemetryReplicationTransport)


def test_response_and_replication_contracts_reject_automatic_enforcement_or_command_like_replication():
    with pytest.raises(ValidationError):
        ResponseAutomationPolicy.model_validate({**_policy().model_dump(), "requires_approval": False})
    with pytest.raises(ValidationError):
        ResponseAutomationPolicy.model_validate({**_policy().model_dump(), "automatic_enforcement": True})
    with pytest.raises(ValidationError):
        TelemetryReplicationTarget.model_validate({**_target().model_dump(), "telemetry_only": False})


@pytest.mark.asyncio
async def test_response_policy_creates_audited_approval_required_request_but_never_executes_an_adapter():
    sessions, engine = await _sessions()
    try:
        policies = ResponseAutomationPolicyRepository(sessions)
        await policies.upsert(_policy())
        containment = GovernedContainmentService(
            sessions,
            audit_signing_key="response-automation-test-hmac",
            audit_key_id="test-key",
        )
        proposals = GovernedResponseProposalService(policies, containment)

        requests = await proposals.propose_for_detection(_detection())
        repeated = await proposals.propose_for_detection(_detection())

        assert len(requests) == 1
        assert requests[0].requires_approval is True
        assert requests[0].automatic_enforcement is False
        assert requests[0].requested_by.startswith("response-policy:")
        assert repeated[0].request_id == requests[0].request_id
        async with sessions() as session:
            executions = (await session.scalars(select(ContainmentExecutionRow))).all()
            assert executions == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_response_policy_fails_closed_without_signed_audit_and_observer_preserves_detection_flow():
    sessions, engine = await _sessions()
    try:
        policies = ResponseAutomationPolicyRepository(sessions)
        await policies.upsert(_policy())
        proposals = GovernedResponseProposalService(policies, GovernedContainmentService(sessions, audit_signing_key=None, audit_key_id=None))
        with pytest.raises(PermissionError, match="HMAC-signed audit"):
            await proposals.propose_for_detection(_detection())
        assert await ResponseProposalObserver(proposals).observe(_detection()) == []

        await policies.upsert(_policy(OTHER_TENANT_ID))
        assert len(await policies.list_for_tenant(TENANT_ID)) == 1
        assert len(await policies.list_for_tenant(OTHER_TENANT_ID)) == 1
    finally:
        await engine.dispose()


class RecordingTransport:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.deliveries = []

    async def deliver(self, target, event) -> None:
        if self.fail:
            raise RuntimeError("regional transport unavailable")
        self.deliveries.append((target.target_id, event.event_id))


@pytest.mark.asyncio
async def test_telemetry_replication_is_tenant_scoped_idempotent_and_records_delivery_receipts():
    sessions, engine = await _sessions()
    try:
        repository = TelemetryReplicationRepository(sessions)
        target = await repository.upsert_target(_target())
        await repository.upsert_target(_target(OTHER_TENANT_ID, "ap-south-1"))
        transport = RecordingTransport()
        service = TelemetryReplicationService(repository, transport, source_region="us-east-1")
        event = _event()

        first = await service.replicate_event(event)
        repeated = await service.replicate_event(event)

        assert len(first) == 1
        assert first[0].status == "delivered"
        assert first[0].target_id == target.target_id
        assert len(first[0].payload_hash) == 64
        assert repeated[0].receipt_id == first[0].receipt_id
        assert repeated[0].attempt_count == 1
        assert transport.deliveries == [(target.target_id, "event-replication-1")]
        assert len(await repository.list_receipts(TENANT_ID)) == 1
        assert await repository.list_receipts(OTHER_TENANT_ID) == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_failed_replication_receipt_can_retry_on_later_canonical_delivery_without_changing_hash_or_tenant():
    sessions, engine = await _sessions()
    try:
        repository = TelemetryReplicationRepository(sessions)
        await repository.upsert_target(_target())
        failed_service = TelemetryReplicationService(repository, RecordingTransport(fail=True), source_region="us-east-1")
        event = _event()
        failed = (await failed_service.replicate_event(event))[0]

        healthy_transport = RecordingTransport()
        healthy_service = TelemetryReplicationService(repository, healthy_transport, source_region="us-east-1")
        recovered = (await healthy_service.replicate_event(event))[0]

        assert failed.status == "failed"
        assert failed.error_code == "RuntimeError"
        assert recovered.receipt_id == failed.receipt_id
        assert recovered.status == "delivered"
        assert recovered.attempt_count == 2
        assert recovered.payload_hash == failed.payload_hash
        assert healthy_transport.deliveries == [(recovered.target_id, "event-replication-1")]
    finally:
        await engine.dispose()


def test_response_and_replication_operations_routes_are_wired_without_new_execution_routes():
    from backend_api.correlation_engine.app import app

    paths = {route.path for route in app.routes}
    assert "/response-policies" in paths
    assert "/telemetry-replication/targets" in paths
    assert "/telemetry-replication/receipts" in paths
    assert not any("execute" in path or "rollback" in path for path in paths if "telemetry-replication" in path or "response-policies" in path)
