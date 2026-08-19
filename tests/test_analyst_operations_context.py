from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.bas_engine.detection_pipeline import run_baseline_detection
from backend_api.case_management_service.workflow import CaseWorkflow
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.evidence_vault.integration import EvidenceIntegrationService, IntegratedEvidenceRepository
from backend_api.shared.database import Base
from backend_api.threat_hunting_service.service import HuntFilter, HuntRequest, ThreatHuntingService
from phantomnet_core.contracts import IntegratedEvidenceRecord


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"
CORRELATION_ID = "phase5-correlation-001"


async def _seed_analyst_context():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    detections = run_baseline_detection(TENANT_ID, CORRELATION_ID)
    detection_repository = DetectionRepository(sessions)
    alert_workflow = AlertWorkflow(sessions)
    for detection in detections:
        stored, created = await detection_repository.persist(detection)
        assert created
        await alert_workflow.ingest_detection(stored)
    alert = (await alert_workflow.list_for_tenant(TENANT_ID))[0]
    case, created = await CaseWorkflow(sessions).create_from_alert(TENANT_ID, alert.alert_id, "phase5-analyst")
    assert created

    evidence_service = EvidenceIntegrationService(IntegratedEvidenceRepository(sessions))
    linked_detection = next(detection for detection in detections if detection.detection_id == alert.detection_ids[0])
    await evidence_service.ingest(
        IntegratedEvidenceRecord(
            tenant_id=TENANT_ID,
            source_kind="wazuh",
            source_name="wazuh-forwarder",
            source_record_id=linked_detection.event_id,
            observed_at=datetime(2026, 8, 19, 14, 0, tzinfo=timezone.utc),
            payload={"integrity": {"event": "modified", "path": "/etc/passwd"}},
            tags=["integrity", "wazuh"],
            provenance={"adapter": "wazuh-read-only", "read_only": True},
        )
    )
    await evidence_service.ingest(
        IntegratedEvidenceRecord(
            tenant_id=TENANT_ID,
            source_kind="graph",
            source_name="attack-path-projection",
            source_record_id=CORRELATION_ID,
            observed_at=datetime(2026, 8, 19, 14, 1, tzinfo=timezone.utc),
            payload={"path": {"node_count": 3, "relationship": "CONNECTED_TO"}},
            tags=["graph", "context"],
            provenance={"adapter": "graph-read-only", "read_only": True},
        )
    )
    return ThreatHuntingService(sessions), alert, case, engine


@pytest.mark.asyncio
async def test_evidence_hunts_and_dashboard_health_remain_tenant_scoped_and_read_only():
    service, _alert, _case, engine = await _seed_analyst_context()
    try:
        evidence_hunt = await service.hunt(
            TENANT_ID,
            HuntRequest(dataset="evidence", filters=[HuntFilter(field="source_kind", operator="in", value=["wazuh", "graph"])]),
        )
        summary = await service.dashboard_summary(TENANT_ID)

        assert evidence_hunt["result_count"] == 2
        assert {record["source_kind"] for record in evidence_hunt["results"]} == {"wazuh", "graph"}
        assert all(record["read_only"] and not record["automatic_enforcement"] for record in evidence_hunt["results"])
        assert evidence_hunt["automated_actions"] == []
        assert summary["metrics"]["integrated_evidence"] == 2
        assert summary["evidence_by_source"] == [
            {"source_kind": "graph", "count": 1},
            {"source_kind": "wazuh", "count": 1},
        ]
        assert summary["automatic_enforcement"] is False
        assert (await service.hunt(OTHER_TENANT_ID, HuntRequest(dataset="evidence")))["results"] == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_alert_and_case_contexts_provide_explainable_evidence_to_decision_trace_without_response_authority():
    service, alert, case, engine = await _seed_analyst_context()
    try:
        alert_context = await service.analyst_context_for_alert(TENANT_ID, alert.alert_id)
        case_context = await service.analyst_context_for_case(TENANT_ID, case.case_id)

        assert alert_context["alert"]["alert_id"] == alert.alert_id
        assert len(alert_context["linked_detections"]) == 1
        assert {record["source_kind"] for record in alert_context["integrated_evidence"]} == {"wazuh", "graph"}
        assert len(alert_context["graph_context"]) == 1
        assert alert_context["priority"]["score"] > 0
        assert {factor["factor"] for factor in alert_context["priority"]["factors"]} == {
            "alert_severity",
            "occurrence_count",
            "linked_detections",
            "endpoint_or_wazuh_evidence",
            "graph_context",
        }
        assert alert_context["recommended_next_step"] == "human_review_required"
        assert alert_context["response_authority"] is False
        assert alert_context["automatic_enforcement"] is False
        assert case_context["case"]["case_id"] == case.case_id
        assert case_context["traceability"]["alert_ids"] == [alert.alert_id]
        assert len(case_context["integrated_evidence"]) == 2
        assert case_context["response_authority"] is False
        with pytest.raises(LookupError):
            await service.analyst_context_for_alert(OTHER_TENANT_ID, alert.alert_id)
        with pytest.raises(LookupError):
            await service.analyst_context_for_case(OTHER_TENANT_ID, case.case_id)
    finally:
        await engine.dispose()


def test_analyst_context_routes_are_read_only_and_exclude_response_operations():
    from backend_api.threat_hunting_service.main import app

    paths = {route.path for route in app.routes}
    assert "/analyst-context/alerts/{alert_id}" in paths
    assert "/analyst-context/cases/{case_id}" in paths
    assert not any("contain" in path or "response" in path for path in paths if "analyst-context" in path)
