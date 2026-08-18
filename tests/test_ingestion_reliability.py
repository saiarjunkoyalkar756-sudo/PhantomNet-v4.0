from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.correlation_engine.ingestion_reliability import (
    BrokerDeliveryRecordedError,
    IngestionDeadLetterRepository,
    ReliableCanonicalIngestion,
)
from backend_api.shared.database import Base
from phantomnet_core.contracts import BrokerDeliveryMetadata


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


def _message(tenant_id: str = TENANT_ID, event_id: str = "event-dead-letter-001"):
    return {
        "schema_version": "1.0.0",
        "event_id": event_id,
        "tenant_id": tenant_id,
        "source": "integration-test",
        "event_type": "process.start",
        "payload": {"hostname": "test-host", "pid": 1234},
    }


def _delivery(offset: int = 1):
    return BrokerDeliveryMetadata(topic="phantomnet.normalized_events", partition=0, offset=offset)


async def _repository():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    return IngestionDeadLetterRepository(sessions), engine


@pytest.mark.asyncio
async def test_dead_letter_failure_receipt_is_idempotent_by_broker_coordinates_and_tenant_scoped():
    repository, engine = await _repository()
    try:
        first, created = await repository.record_failure(_message(), _delivery(), ValueError("invalid envelope"))
        duplicate, duplicate_created = await repository.record_failure(_message(), _delivery(), RuntimeError("retry exhausted"))

        assert created is True
        assert duplicate_created is False
        assert duplicate.dead_letter_id == first.dead_letter_id
        assert duplicate.attempt_count == 2
        assert duplicate.error_code == "CANONICAL_PROCESSING_FAILED"
        assert duplicate.status == "open"
        assert len(duplicate.message_hash) == 64
        assert [record.dead_letter_id for record in await repository.list_for_tenant(TENANT_ID)] == [first.dead_letter_id]
        assert await repository.list_for_tenant(OTHER_TENANT_ID) == []
    finally:
        await engine.dispose()

@pytest.mark.asyncio
async def test_dead_letter_refuses_coordinate_reuse_with_a_different_message_and_does_not_trust_invalid_tenant_values():
    repository, engine = await _repository()
    try:
        await repository.record_failure(_message(), _delivery(), ValueError("invalid"))
        conflicting = _message(event_id="event-dead-letter-conflict")
        with pytest.raises(ValueError, match="reused with a different message hash"):
            await repository.record_failure(conflicting, _delivery(), ValueError("invalid"))

        invalid_tenant, created = await repository.record_failure(
            _message(tenant_id="untrusted-not-a-uuid", event_id="event-invalid-tenant"),
            _delivery(offset=2),
            ValueError("invalid"),
        )
        assert created is True
        assert invalid_tenant.tenant_id is None
        assert await repository.list_for_tenant(TENANT_ID) != []
        assert await repository.list_for_tenant(OTHER_TENANT_ID) == []
    finally:
        await engine.dispose()

@pytest.mark.asyncio
async def test_reliable_processor_records_failure_and_explicit_replay_marks_receipt_replayed_once():
    repository, engine = await _repository()
    calls = []

    async def failing_processor(message):
        raise ValueError("poison message")

    async def successful_processor(message):
        calls.append(message["event_id"])
        return {"accepted": True}

    reliability = ReliableCanonicalIngestion(failing_processor, repository)
    try:
        with pytest.raises(BrokerDeliveryRecordedError, match="dead-letter evidence") as failure:
            await reliability.process_delivery(_message(), _delivery())
        receipt = failure.value.receipt
        assert receipt.error_code == "CANONICAL_VALIDATION_FAILED"
        assert receipt.error_type == "ValueError"

        replayed = await repository.replay(TENANT_ID, receipt.dead_letter_id, "analyst-1", successful_processor)
        replayed_again = await repository.replay(TENANT_ID, receipt.dead_letter_id, "analyst-2", successful_processor)

        assert replayed.status == "replayed"
        assert replayed.replayed_by == "analyst-1"
        assert replayed_again.replayed_by == "analyst-1"
        assert calls == ["event-dead-letter-001"]
    finally:
        await engine.dispose()

@pytest.mark.asyncio
async def test_replay_failure_retains_open_receipt_increments_attempts_and_never_changes_tenant_scope():
    repository, engine = await _repository()

    async def failing_processor(message):
        raise RuntimeError("still poison")

    try:
        receipt, _ = await repository.record_failure(_message(), _delivery(), ValueError("first failure"))
        with pytest.raises(RuntimeError, match="still poison"):
            await repository.replay(TENANT_ID, receipt.dead_letter_id, "analyst-1", failing_processor)

        current = (await repository.list_for_tenant(TENANT_ID))[0]
        assert current.status == "open"
        assert current.attempt_count == 2
        assert current.replayed_by is None
        with pytest.raises(LookupError, match="authenticated tenant"):
            await repository.replay(OTHER_TENANT_ID, receipt.dead_letter_id, "analyst-2", failing_processor)
    finally:
        await engine.dispose()
