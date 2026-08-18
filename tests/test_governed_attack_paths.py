"""Isolated tests for the read-only governed attack-path analysis service."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend_api.attack_graph_engine.governed_attack_paths import (
    AttackPathQuery,
    GovernedAttackPathService,
)
from phantomnet_core.contracts import (
    AlertRecord,
    CaseRecord,
    DetectionRecord,
    HostAssetRecord,
    IntegrityObservation,
    MitreEvidence,
)


TENANT_A = "00000000-0000-0000-0000-000000000001"
TENANT_B = "00000000-0000-0000-0000-000000000002"


def _tenant_evidence(tenant_id: str, suffix: str):
    asset = HostAssetRecord(
        asset_id=f"asset-{suffix}",
        tenant_id=tenant_id,
        agent_id=f"agent-{suffix}",
        hostname=f"host-{suffix}",
        platform="linux",
        source="wazuh",
    )
    integrity = IntegrityObservation(
        observation_id=f"integrity-{suffix}",
        tenant_id=tenant_id,
        asset_id=asset.asset_id,
        agent_id=asset.agent_id,
        source_event_id=f"event-{suffix}",
        source="wazuh",
        check_type="file",
        status="modified",
        severity="high",
        path=f"/tmp/{suffix}.txt",
    )
    detection = DetectionRecord(
        detection_id=f"detection-{suffix}",
        tenant_id=tenant_id,
        event_id=integrity.source_event_id,
        rule_id="governed.test.integrity",
        rule_version="1.0.0",
        severity="high",
        title=f"Integrity detection {suffix}",
        evidence={"asset_id": asset.asset_id, "source": "controlled-test"},
        mitre_evidence=[
            MitreEvidence(
                technique_id="T1565.001",
                tactic="impact",
                confidence=1.0,
                rationale="Controlled graph evidence fixture.",
                evidence_fields=["asset_id"],
            )
        ],
    )
    alert = AlertRecord(
        alert_id=f"alert-{suffix}",
        tenant_id=tenant_id,
        detection_ids=[detection.detection_id],
        title=f"Integrity alert {suffix}",
        severity="high",
        suppression_key=f"suppression-{suffix}",
    )
    case = CaseRecord(
        case_id=f"case-{suffix}",
        tenant_id=tenant_id,
        alert_ids=[alert.alert_id],
        title=f"Investigation {suffix}",
        severity="high",
        created_by="test-analyst",
    )
    return asset, integrity, detection, alert, case


@pytest.mark.asyncio
async def test_governed_attack_path_is_evidence_bound_read_only_and_tenant_scoped():
    service = GovernedAttackPathService()
    asset, integrity, detection, alert, case = _tenant_evidence(TENANT_A, "tenant-a")

    projection = await service.project_evidence(
        TENANT_A,
        assets=[asset],
        integrity_observations=[integrity],
        detections=[detection],
        alerts=[alert],
        cases=[case],
    )
    analysis = await service.analyze(
        TENANT_A,
        AttackPathQuery(
            source_node_id=f"case:{case.case_id}",
            target_node_id=f"asset:{asset.asset_id}",
            max_hops=4,
        ),
    )

    assert projection.node_count == 6
    assert projection.edge_count == 6
    assert analysis.analysis_mode == "read_only"
    assert len(analysis.paths) == 2
    path = next(path for path in analysis.paths if path.hop_count == 4)
    assert path.node_ids == [
        f"case:{case.case_id}",
        f"alert:{alert.alert_id}",
        f"detection:{detection.detection_id}",
        f"integrity:{integrity.observation_id}",
        f"asset:{asset.asset_id}",
    ]
    assert path.hop_count == 4
    assert {case.case_id, alert.alert_id, detection.detection_id, integrity.observation_id, asset.asset_id}.issubset(path.evidence_ids)
    assert not hasattr(service, "execute")
    assert not hasattr(service, "rollback")


@pytest.mark.asyncio
async def test_governed_attack_paths_refuse_cross_tenant_projection_and_queries():
    service = GovernedAttackPathService()
    asset_a, integrity_a, detection_a, alert_a, case_a = _tenant_evidence(TENANT_A, "tenant-a")
    asset_b, integrity_b, detection_b, alert_b, case_b = _tenant_evidence(TENANT_B, "tenant-b")

    await service.project_evidence(
        TENANT_A,
        assets=[asset_a],
        integrity_observations=[integrity_a],
        detections=[detection_a],
        alerts=[alert_a],
        cases=[case_a],
    )
    await service.project_evidence(
        TENANT_B,
        assets=[asset_b],
        integrity_observations=[integrity_b],
        detections=[detection_b],
        alerts=[alert_b],
        cases=[case_b],
    )

    with pytest.raises(LookupError, match="authenticated tenant"):
        await service.analyze(
            TENANT_B,
            AttackPathQuery(source_node_id=f"case:{case_a.case_id}", target_node_id=f"asset:{asset_a.asset_id}"),
        )
    with pytest.raises(ValueError, match="cross-tenant evidence"):
        await service.project_evidence(
            TENANT_A,
            assets=[asset_b],
            integrity_observations=[],
            detections=[],
            alerts=[],
            cases=[],
        )


def test_governed_attack_path_query_is_bounded_and_rejects_undeclared_input():
    with pytest.raises(ValidationError):
        AttackPathQuery(source_node_id="case:one", target_node_id="asset:two", max_hops=7)
    with pytest.raises(ValidationError):
        AttackPathQuery(source_node_id="case:one", target_node_id="asset:two", cypher="MATCH (n) RETURN n")
    with pytest.raises(ValidationError):
        AttackPathQuery(source_node_id="case:one", target_node_id="case:one")


def test_governed_attack_path_router_is_wired_under_the_api_prefix():
    from backend_api.attack_graph_engine.main import app

    paths = {route.path for route in app.routes}
    assert "/api/governed-attack-paths/refresh" in paths
    assert "/api/governed-attack-paths/analyze" in paths


@pytest.mark.asyncio
async def test_legacy_unscoped_graph_route_is_disabled():
    from fastapi import HTTPException

    from backend_api.attack_graph_engine.main import PathRequest, find_attack_paths

    with pytest.raises(HTTPException) as exc_info:
        await find_attack_paths(PathRequest(source_node="legacy-source", target_node="legacy-target"))
    assert exc_info.value.status_code == 410
    assert "governed-attack-paths" in exc_info.value.detail
