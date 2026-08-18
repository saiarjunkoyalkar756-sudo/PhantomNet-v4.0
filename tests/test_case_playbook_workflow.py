import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.bas_engine.detection_pipeline import run_baseline_detection
from backend_api.case_management_service.workflow import CaseWorkflow
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.shared.database import Base


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"
CORRELATION_ID = "corr-case-lifecycle-001"


async def _isolated_workflows():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    return AlertWorkflow(sessions), CaseWorkflow(sessions), engine


@pytest.mark.asyncio
async def test_alert_to_case_linkage_preserves_detection_and_mitre_evidence():
    alert_workflow, case_workflow, engine = await _isolated_workflows()
    try:
        detection = run_baseline_detection(TENANT_ID, CORRELATION_ID)[0]
        alert_result = await alert_workflow.ingest_detection(detection)

        case, created = await case_workflow.create_from_alert(TENANT_ID, alert_result.alert.alert_id, "analyst-1")
        repeat_case, created_again = await case_workflow.create_from_alert(TENANT_ID, alert_result.alert.alert_id, "analyst-1")

        assert created is True
        assert created_again is False
        assert repeat_case.case_id == case.case_id
        assert case.alert_ids == [alert_result.alert.alert_id]
        assert case.status == "triaged"
        assert case.evidence["detection_ids"] == [detection.detection_id]
        assert case.evidence["mitre_evidence"][0]["technique_id"] == "T1110"
        updated_alert = (await alert_workflow.list_for_tenant(TENANT_ID))[0]
        assert updated_alert.case_id == case.case_id
        assert updated_alert.status == "triaged"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_case_and_playbook_lifecycle_enforce_approval_before_running_without_dispatch():
    alert_workflow, case_workflow, engine = await _isolated_workflows()
    try:
        detection = run_baseline_detection(TENANT_ID, CORRELATION_ID)[0]
        alert = (await alert_workflow.ingest_detection(detection)).alert
        case, _ = await case_workflow.create_from_alert(TENANT_ID, alert.alert_id, "analyst-1")

        in_progress = await case_workflow.transition_case(TENANT_ID, case.case_id, "in_progress", "analyst-1")
        assert in_progress.status == "in_progress"

        run = await case_workflow.request_playbook(
            TENANT_ID, case.case_id, "containment.review", "1.0.0", "analyst-1"
        )
        assert run.status == "awaiting_approval"
        assert run.evidence["execution_dispatched"] is False
        with pytest.raises(ValueError, match="Invalid playbook lifecycle transition"):
            await case_workflow.transition_playbook(TENANT_ID, run.run_id, "running", "analyst-1")

        approved = await case_workflow.transition_playbook(TENANT_ID, run.run_id, "approved", "admin-1")
        running = await case_workflow.transition_playbook(TENANT_ID, run.run_id, "running", "analyst-1")
        completed = await case_workflow.transition_playbook(TENANT_ID, run.run_id, "completed", "analyst-1")

        assert approved.approved_by == "admin-1"
        assert running.started_at is not None
        assert completed.completed_at is not None
        assert completed.status == "completed"
        assert completed.evidence["execution_dispatched"] is False
        assert (await case_workflow.list_playbook_runs(TENANT_ID, case.case_id))[0].run_id == run.run_id
        updated_case = await case_workflow.get_case(TENANT_ID, case.case_id)
        assert [entry["action"] for entry in updated_case.timeline].count("playbook_requested") == 1
        assert [entry["action"] for entry in updated_case.timeline].count("playbook_status_changed") == 3
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_case_and_playbook_records_are_tenant_scoped():
    alert_workflow, case_workflow, engine = await _isolated_workflows()
    try:
        detection = run_baseline_detection(TENANT_ID, CORRELATION_ID)[0]
        alert = (await alert_workflow.ingest_detection(detection)).alert
        case, _ = await case_workflow.create_from_alert(TENANT_ID, alert.alert_id, "analyst-1")

        with pytest.raises(LookupError):
            await case_workflow.get_case(OTHER_TENANT_ID, case.case_id)
        with pytest.raises(LookupError):
            await case_workflow.create_from_alert(OTHER_TENANT_ID, alert.alert_id, "analyst-2")
        with pytest.raises(ValueError, match="Invalid case lifecycle transition"):
            await case_workflow.transition_case(TENANT_ID, case.case_id, "new", "analyst-1")
    finally:
        await engine.dispose()
