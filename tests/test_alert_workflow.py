from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.bas_engine.detection_pipeline import run_baseline_detection
from backend_api.bas_engine.baseline_scenarios import emit_baseline_events
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base
from phantomnet_core.contracts import DetectionRecord


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"
CORRELATION_ID = "corr-alert-workflow-001"


async def _isolated_workflow():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    return DetectionRepository(sessions), AlertWorkflow(sessions, suppression_window_seconds=900), engine


def _controlled_detection() -> DetectionRecord:
    return run_baseline_detection(TENANT_ID, CORRELATION_ID)[0]


def _repeat_of(detection: DetectionRecord) -> DetectionRecord:
    return detection.model_copy(update={"detection_id": str(uuid4()), "event_id": str(uuid4())})


def test_baseline_detections_include_validated_mitre_evidence():
    detections = run_baseline_detection(TENANT_ID, CORRELATION_ID)

    assert len(detections) == 5
    assert {detection.mitre_evidence[0].technique_id for detection in detections} == {
        "T1110",
        "T1059",
        "T1071.004",
        "T1071.001",
        "T1565.001",
    }
    assert all(evidence.confidence == 1.0 for detection in detections for evidence in detection.mitre_evidence)
    assert all(detection.automatic_enforcement is False for detection in detections)


@pytest.mark.asyncio
async def test_alert_workflow_suppresses_repeated_governed_evidence_and_keeps_one_active_alert():
    _repository, workflow, engine = await _isolated_workflow()
    try:
        first = _controlled_detection()
        repeated = _repeat_of(first)

        first_result = await workflow.ingest_detection(first)
        repeated_result = await workflow.ingest_detection(repeated)
        alerts = await workflow.list_for_tenant(TENANT_ID)

        assert first_result.created is True
        assert first_result.suppressed is False
        assert repeated_result.created is False
        assert repeated_result.suppressed is True
        assert len(alerts) == 1
        assert alerts[0].status == "new"
        assert alerts[0].occurrence_count == 2
        assert alerts[0].detection_ids == [first.detection_id, repeated.detection_id]
        assert alerts[0].mitre_evidence[0].technique_id == "T1110"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_alert_workflow_enforces_lifecycle_and_tenant_isolation():
    _repository, workflow, engine = await _isolated_workflow()
    try:
        created = await workflow.ingest_detection(_controlled_detection())
        alert_id = created.alert.alert_id

        triaged = await workflow.transition(TENANT_ID, alert_id, "triaged", actor="analyst-1", case_id="case-123")
        assert triaged.status == "triaged"
        assert triaged.triaged_by == "analyst-1"
        assert triaged.case_id == "case-123"
        assert await workflow.list_for_tenant(OTHER_TENANT_ID) == []

        with pytest.raises(LookupError):
            await workflow.transition(OTHER_TENANT_ID, alert_id, "triaged", actor="analyst-2")
        with pytest.raises(ValueError, match="Invalid alert lifecycle transition"):
            await workflow.transition(TENANT_ID, alert_id, "new", actor="analyst-1")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canonical_broker_processor_creates_one_alert_after_new_detection_persistence():
    repository, workflow, engine = await _isolated_workflow()
    try:
        raw_event = emit_baseline_events(TENANT_ID, CORRELATION_ID)[0]
        normalized = normalize_event(raw_event.model_dump(mode="json"))
        processor = CanonicalBrokerProcessor(repository, alert_workflow=workflow)

        first_delivery = await processor.process(normalized)
        retry_delivery = await processor.process(normalized)

        assert len(first_delivery.alert_workflows) == 1
        assert first_delivery.alert_workflows[0].created is True
        assert retry_delivery.alert_workflows == ()
        alerts = await workflow.list_for_tenant(TENANT_ID)
        assert len(alerts) == 1
        assert alerts[0].detection_ids == list(first_delivery.created_detection_ids)
    finally:
        await engine.dispose()
