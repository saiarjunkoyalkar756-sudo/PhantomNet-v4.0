import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.bas_engine.detection_pipeline import run_baseline_detection
from backend_api.case_management_service.workflow import CaseWorkflow
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.shared.database import Base
from backend_api.threat_hunting_service.service import (
    HuntFilter,
    HuntRequest,
    SavedHuntCreate,
    ThreatHuntingService,
)


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"
CORRELATION_ID = "corr-hunt-001"


async def _seed_hunt_data():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    detection_repository = DetectionRepository(sessions)
    alert_workflow = AlertWorkflow(sessions)
    case_workflow = CaseWorkflow(sessions)
    detections = run_baseline_detection(TENANT_ID, CORRELATION_ID)
    for detection in detections:
        stored, created = await detection_repository.persist(detection)
        assert created
        await alert_workflow.ingest_detection(stored)
    first_alert = (await alert_workflow.list_for_tenant(TENANT_ID))[0]
    await case_workflow.create_from_alert(TENANT_ID, first_alert.alert_id, "analyst-1")
    return ThreatHuntingService(sessions), engine


@pytest.mark.asyncio
async def test_governed_hunt_supports_only_allowlisted_fields_and_tenant_scoped_results():
    service, engine = await _seed_hunt_data()
    try:
        result = await service.hunt(
            TENANT_ID,
            HuntRequest(
                dataset="detections",
                filters=[HuntFilter(field="mitre_technique", operator="eq", value="T1071.004")],
            ),
        )
        assert result["result_count"] == 1
        assert result["results"][0]["mitre_evidence"][0]["technique_id"] == "T1071.004"
        assert result["automated_actions"] == []
        assert await service.hunt(OTHER_TENANT_ID, HuntRequest(dataset="detections")) == {
            "dataset": "detections",
            "filters": [],
            "result_count": 0,
            "results": [],
            "automated_actions": [],
            "note": "Hunts are read-only and do not dispatch containment or response actions.",
        }
        with pytest.raises(ValueError, match="cannot be searched"):
            await service.hunt(
                TENANT_ID,
                HuntRequest(dataset="alerts", filters=[HuntFilter(field="tenant_id", operator="eq", value=TENANT_ID)]),
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_saved_hunts_and_automated_templates_run_against_canonical_data_without_actions():
    service, engine = await _seed_hunt_data()
    try:
        saved = await service.create_saved_hunt(
            TENANT_ID,
            "analyst-1",
            SavedHuntCreate(
                name="C2 focus",
                description="Find ATT&CK DNS and web protocol activity.",
                dataset="detections",
                filters=[HuntFilter(field="mitre_technique", operator="in", value=["T1071.001", "T1071.004"])],
            ),
        )
        listed = await service.list_saved_hunts(TENANT_ID)
        executed = await service.run_saved_hunt(TENANT_ID, saved.hunt_id)
        automated = await service.automated_hunts(TENANT_ID)

        assert listed[0].hunt_id == saved.hunt_id
        assert executed["result_count"] == 2
        assert automated["command-and-control-mitre"]["result_count"] == 2
        assert automated["high-severity-unresolved"]["automated_actions"] == []
        with pytest.raises(LookupError):
            await service.run_saved_hunt(OTHER_TENANT_ID, saved.hunt_id)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_dashboard_summary_aggregates_real_tenant_owned_soc_records():
    service, engine = await _seed_hunt_data()
    try:
        summary = await service.dashboard_summary(TENANT_ID)

        assert summary["metrics"]["detections"] == 5
        assert summary["metrics"]["active_alerts"] == 5
        assert summary["metrics"]["open_cases"] == 1
        assert {item["technique_id"] for item in summary["top_mitre_techniques"]} == {
            "T1110", "T1059", "T1071.004", "T1071.001", "T1565.001"
        }
    finally:
        await engine.dispose()
