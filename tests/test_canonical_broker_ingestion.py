from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.bas_engine.baseline_scenarios import emit_baseline_events
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base
from phantomnet_core.contracts import DetectionRecord


TENANT_ID = "00000000-0000-0000-0000-000000000001"
CORRELATION_ID = "corr-broker-001"


async def _isolated_repository():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return DetectionRepository(async_sessionmaker(engine, expire_on_commit=False)), engine


def _normalized_auth_scenario():
    event = emit_baseline_events(TENANT_ID, CORRELATION_ID)[0]
    return normalize_event(event.model_dump(mode="json"))


@pytest.mark.asyncio
async def test_canonical_broker_delivery_persists_one_tenant_scoped_detection_and_deduplicates_retries():
    repository, engine = await _isolated_repository()
    try:
        processor = CanonicalBrokerProcessor(repository)
        normalized = _normalized_auth_scenario()

        first_delivery = await processor.process(normalized)
        retry_delivery = await processor.process(normalized)
        stored = await DetectionRepository(repository._session_factory).list_for_tenant(TENANT_ID)

        assert len(first_delivery.persisted_detections) == 1
        assert len(first_delivery.created_detection_ids) == 1
        assert first_delivery.duplicate_detection_ids == ()
        assert retry_delivery.created_detection_ids == ()
        assert retry_delivery.duplicate_detection_ids == first_delivery.created_detection_ids
        assert len(stored) == 1
        assert stored[0].tenant_id == TENANT_ID
        assert stored[0].event_id == normalized["event_id"]
        assert stored[0].correlation_id == CORRELATION_ID
        assert stored[0].automatic_enforcement is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canonical_broker_processor_rejects_invalid_envelopes_before_storage():
    repository, engine = await _isolated_repository()
    try:
        processor = CanonicalBrokerProcessor(repository)
        with pytest.raises(ValidationError):
            await processor.process({"event_id": "missing-required-contract-fields"})
        assert await repository.list_for_tenant(TENANT_ID) == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canonical_broker_processor_rejects_detection_not_bound_to_source_event():
    repository, engine = await _isolated_repository()
    try:
        normalized = _normalized_auth_scenario()

        def mismatched_evaluator(_message):
            return DetectionRecord(
                detection_id=str(uuid4()),
                rule_id="test.mismatched",
                rule_version="1.0.0",
                event_id="other-event",
                tenant_id=TENANT_ID,
                correlation_id=CORRELATION_ID,
                severity="high",
                title="Invalid binding",
            )

        processor = CanonicalBrokerProcessor(repository, evaluators=(mismatched_evaluator,))
        with pytest.raises(ValueError, match="event_id"):
            await processor.process(normalized)
        assert await repository.list_for_tenant(TENANT_ID) == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_correlation_consumer_routes_broker_message_through_canonical_processor(monkeypatch):
    from backend_api.correlation_engine import consumer
    from backend_api.correlation_engine.ingestion import BrokerIngestionResult
    from phantomnet_core.contracts import EventEnvelope

    normalized = _normalized_auth_scenario()
    expected_result = BrokerIngestionResult(
        event=EventEnvelope.model_validate(normalized),
        persisted_detections=(),
        created_detection_ids=(),
        duplicate_detection_ids=(),
    )

    class RecordingProcessor:
        def __init__(self):
            self.messages = []

        async def process(self, message):
            self.messages.append(message)
            return expected_result

    processor = RecordingProcessor()
    monkeypatch.setattr(consumer, "broker_processor", processor)

    async def no_mitre(_event):
        return []

    async def no_rules():
        return []

    class NoEnricher:
        async def enrich_indicator(self, _indicator, _indicator_type):
            return None

    monkeypatch.setattr(consumer, "map_event_with_mitre", no_mitre)
    monkeypatch.setattr(consumer, "get_all_rules", no_rules)
    monkeypatch.setattr(consumer, "ti_enricher", NoEnricher())

    result = await consumer._process_event_async(normalized)

    assert result is expected_result
    assert processor.messages == [normalized]
