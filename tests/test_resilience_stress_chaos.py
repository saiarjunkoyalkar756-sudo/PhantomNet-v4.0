"""Controlled resilience tests for in-memory canonical processing only.

These tests inject local software failures into repositories and workflows. They do not contact a
broker, cloud account, endpoint, or external network and they never execute a response adapter.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from statistics import median

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.correlation_engine.ingestion_reliability import (
    BrokerDeliveryRecordedError,
    IngestionDeadLetterRepository,
    ReliableCanonicalIngestion,
)
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base
from phantomnet_core.contracts import BrokerDeliveryMetadata, EventEnvelope


TENANT_ID = "00000000-0000-0000-0000-000000000001"


async def _environment(repository_type=DetectionRepository, workflow_type=AlertWorkflow):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = repository_type(sessions)
    workflow = workflow_type(sessions)
    processor = CanonicalBrokerProcessor(repository, alert_workflow=workflow)
    return engine, repository, workflow, processor, IngestionDeadLetterRepository(sessions)


def _raw_event(index: int = 0) -> dict:
    return EventEnvelope(
        event_id=f"resilience-event-{index:04d}",
        tenant_id=TENANT_ID,
        timestamp=datetime.now(timezone.utc),
        source="bas-engine",
        event_type="auth_attempt",
        severity="high",
        correlation_id=f"resilience-correlation-{index:04d}",
        payload={
            "scenario_id": "BAS-AUTH-001",
            "source_ip": "198.51.100.42",
            "failed_attempts": 5,
            "sample": index,
        },
        tags=["bas", "controlled", "resilience", "non-destructive"],
        provenance={"execution": "telemetry-fixture", "fixture": "stress-chaos"},
    ).model_dump(mode="json")


class FailOnceDetectionRepository(DetectionRepository):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failures_remaining = 1

    async def persist(self, detection):
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise OSError("controlled persistence fault")
        return await super().persist(detection)


class FailOnceAlertWorkflow(AlertWorkflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failures_remaining = 1

    async def ingest_detection(self, detection):
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise RuntimeError("controlled alert workflow fault")
        return await super().ingest_detection(detection)


@pytest.mark.asyncio
async def test_controlled_stress_preserves_unique_detections_and_alerts_under_duplicate_delivery():
    engine, repository, workflow, processor, _dead_letters = await _environment()
    event_count = 200
    timings_ms: list[float] = []
    messages = [normalize_event(_raw_event(index)) for index in range(event_count)]
    try:
        for message in messages:
            started = time.perf_counter()
            result = await processor.process(message)
            timings_ms.append((time.perf_counter() - started) * 1000)
            assert len(result.created_detection_ids) == 1
            assert len(result.alert_workflows) == 1

        for message in messages[::10]:
            duplicate = await processor.process(message)
            assert duplicate.created_detection_ids == ()
            assert len(duplicate.duplicate_detection_ids) == 1
            assert len(duplicate.alert_workflows) == 1

        detections = await repository.list_for_tenant(TENANT_ID, limit=500)
        alerts = await workflow.list_for_tenant(TENANT_ID, limit=500)
        ordered = sorted(timings_ms)
        p95 = ordered[int(len(ordered) * 0.95) - 1]
        assert len(detections) == event_count
        assert len(alerts) == event_count
        assert all(alert.occurrence_count == 1 for alert in alerts)
        assert median(timings_ms) >= 0
        assert p95 < 2_000  # Detect pathological local regressions without claiming production capacity.
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_controlled_persistence_fault_creates_durable_receipt_and_replay_recovers_once():
    engine, repository, workflow, processor, dead_letters = await _environment(FailOnceDetectionRepository)
    reliable = ReliableCanonicalIngestion(processor.process, dead_letters)
    message = normalize_event(_raw_event(301))
    delivery = BrokerDeliveryMetadata(topic="resilience.topic", partition=0, offset=301)
    try:
        with pytest.raises(BrokerDeliveryRecordedError) as exc_info:
            await reliable.process_delivery(message, delivery)
        receipt = exc_info.value.receipt
        assert receipt.error_code == "CANONICAL_PROCESSING_FAILED"
        assert receipt.status == "open"

        replayed = await dead_letters.replay(TENANT_ID, receipt.dead_letter_id, "resilience-analyst", processor.process)
        assert replayed.status == "replayed"
        assert len(await repository.list_for_tenant(TENANT_ID)) == 1
        assert len(await workflow.list_for_tenant(TENANT_ID)) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_controlled_alert_fault_replays_duplicate_detection_without_alert_inflation():
    engine, repository, workflow, processor, dead_letters = await _environment(DetectionRepository, FailOnceAlertWorkflow)
    reliable = ReliableCanonicalIngestion(processor.process, dead_letters)
    message = normalize_event(_raw_event(401))
    delivery = BrokerDeliveryMetadata(topic="resilience.topic", partition=0, offset=401)
    try:
        with pytest.raises(BrokerDeliveryRecordedError) as exc_info:
            await reliable.process_delivery(message, delivery)
        receipt = exc_info.value.receipt

        replayed = await dead_letters.replay(TENANT_ID, receipt.dead_letter_id, "resilience-analyst", processor.process)
        alerts = await workflow.list_for_tenant(TENANT_ID)
        detections = await repository.list_for_tenant(TENANT_ID)
        assert replayed.status == "replayed"
        assert len(detections) == 1
        assert len(alerts) == 1
        assert alerts[0].occurrence_count == 1
    finally:
        await engine.dispose()


class FailOnceRegionalTransport:
    def __init__(self) -> None:
        self.failures_remaining = 1
        self.deliveries: list[str] = []

    async def deliver(self, target, event) -> None:
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise ConnectionError("controlled regional transport fault")
        self.deliveries.append(event.event_id)


@pytest.mark.asyncio
async def test_controlled_regional_transport_fault_records_failure_then_recovers_with_the_same_event_hash():
    from backend_api.correlation_engine.telemetry_replication import (
        TelemetryReplicationRepository,
        TelemetryReplicationService,
    )
    from phantomnet_core.contracts import TelemetryReplicationTarget

    engine, _repository, _workflow, _processor, _dead_letters = await _environment()
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    replication = TelemetryReplicationRepository(sessions)
    transport = FailOnceRegionalTransport()
    try:
        await replication.upsert_target(
            TelemetryReplicationTarget(
                tenant_id=TENANT_ID,
                target_region="chaos-region-1",
                stream_name="phantomnet.telemetry.chaos",
            )
        )
        event = EventEnvelope.model_validate(normalize_event(_raw_event(501)))
        service = TelemetryReplicationService(replication, transport, source_region="chaos-source")
        failed = (await service.replicate_event(event))[0]
        recovered = (await service.replicate_event(event))[0]
        assert failed.status == "failed"
        assert recovered.status == "delivered"
        assert recovered.receipt_id == failed.receipt_id
        assert recovered.payload_hash == failed.payload_hash
        assert recovered.attempt_count == 2
        assert transport.deliveries == [event.event_id]
    finally:
        await engine.dispose()


def test_controlled_audit_tamper_fault_is_detected_without_repairing_evidence():
    from backend_api.audit_log_collector.integrity import append_record, verify_chain

    first = append_record(
        "chaos-audit-1",
        "analyst",
        "containment.requested",
        {"request_id": "r1"},
        signing_key="chaos-key",
        signature_key_id="chaos-key-id",
    )
    second = append_record(
        "chaos-audit-2",
        "approver",
        "containment.approved",
        {"request_id": "r1"},
        previous_hash=first.record_hash,
        signing_key="chaos-key",
        signature_key_id="chaos-key-id",
    )
    records = [first.as_dict(), second.as_dict()]
    assert verify_chain(records, signing_key="chaos-key", require_signature=True, expected_key_id="chaos-key-id")
    records[1]["payload"] = {"request_id": "tampered"}
    assert not verify_chain(records, signing_key="chaos-key", require_signature=True, expected_key_id="chaos-key-id")
