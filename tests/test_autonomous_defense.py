from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.evidence_vault.integration import EvidenceIntegrationService, IntegratedEvidenceRepository
from backend_api.shared.database import (
    AutonomousDefenseDecisionRow,
    Base,
    ContainmentExecutionRow,
)
from backend_api.soar_engine.autonomous_defense import (
    AutonomousDefenseDecisionService,
    AutonomousDefenseObserver,
    AutonomousDefenseRepository,
)
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import (
    AutonomousDefenseDecision,
    AutonomousDefensePolicy,
    DetectionRecord,
    IntegratedEvidenceRecord,
)


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


async def _sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False), engine


def _detection(
    tenant_id: str = TENANT_ID,
    detection_id: str = "autonomous-detection-1",
    severity: str = "high",
    evidence_ids: list[str] | None = None,
) -> DetectionRecord:
    return DetectionRecord(
        detection_id=detection_id,
        rule_id="governed-rule-autonomous-1",
        rule_version="1.0.0",
        event_id=f"event-{detection_id}",
        tenant_id=tenant_id,
        severity=severity,
        title="Evidence-grounded autonomous-defense test detection",
        evidence={"evidence_ids": evidence_ids or []},
    )


def _policy(
    tenant_id: str = TENANT_ID,
    *,
    name: str = "Investigate evidence-grounded high severity detection",
    decision_mode: str = "investigate",
    minimum_evidence_count: int = 1,
    minimum_confidence: float = 0.80,
    required_evidence_kinds: list[str] | None = None,
) -> AutonomousDefensePolicy:
    data = {
        "tenant_id": tenant_id,
        "name": name,
        "trigger_rule_ids": ["governed-rule-autonomous-1"],
        "minimum_severity": "high",
        "decision_mode": decision_mode,
        "minimum_confidence": minimum_confidence,
        "minimum_evidence_count": minimum_evidence_count,
        "required_evidence_kinds": required_evidence_kinds or [],
    }
    if decision_mode == "propose_containment":
        data.update(
            {
                "containment_action": "isolate_endpoint",
                "target": "endpoint-lab-01",
                "asset_id": "asset-lab-01",
            }
        )
    return AutonomousDefensePolicy(**data)


def _evidence(tenant_id: str = TENANT_ID, evidence_id: str = "evidence-autonomous-1") -> IntegratedEvidenceRecord:
    return IntegratedEvidenceRecord(
        evidence_id=evidence_id,
        tenant_id=tenant_id,
        source_kind="endpoint",
        source_name="endpoint-agent",
        source_record_id=f"event-autonomous-detection-1",
        observed_at=datetime.now(timezone.utc),
        payload={"process": "suspicious-tool", "host": "endpoint-lab-01"},
        tags=["endpoint", "test"],
        provenance={"adapter": "test", "read_only": True},
    )


def _service(sessions, *, signing_key: str | None = "autonomous-defense-test-hmac"):
    evidence = EvidenceIntegrationService(IntegratedEvidenceRepository(sessions))
    containment = GovernedContainmentService(
        sessions,
        audit_signing_key=signing_key,
        audit_key_id="autonomous-defense-test-key" if signing_key else None,
    )
    return AutonomousDefenseDecisionService(AutonomousDefenseRepository(sessions), evidence, containment), evidence


def test_autonomous_defense_contracts_reject_automatic_enforcement_and_unapproved_containment():
    policy = _policy()
    with pytest.raises(ValidationError, match="human approval"):
        AutonomousDefensePolicy.model_validate({**policy.model_dump(), "requires_approval": False})
    with pytest.raises(ValidationError, match="automatic high-impact enforcement"):
        AutonomousDefensePolicy.model_validate({**policy.model_dump(), "automatic_enforcement": True})
    with pytest.raises(ValidationError, match="containment_action and target"):
        AutonomousDefensePolicy.model_validate({**policy.model_dump(), "decision_mode": "propose_containment"})
    with pytest.raises(ValidationError, match="human approval"):
        AutonomousDefenseDecision.model_validate(
            {
                "tenant_id": TENANT_ID,
                "policy_id": policy.policy_id,
                "detection_id": "contract-detection-1",
                "rule_id": "governed-rule-autonomous-1",
                "severity": "high",
                "confidence": 0.80,
                "decision_mode": "investigate",
                "outcome": "decision_recorded",
                "reasons": ["contract validation for mandatory approval"],
                "requires_human_approval": False,
            }
        )


@pytest.mark.asyncio
async def test_evidence_grounded_investigation_is_immutable_idempotent_and_tenant_scoped():
    sessions, engine = await _sessions()
    try:
        service, evidence_service = _service(sessions)
        policy = await service._repository.upsert_policy(
            _policy(required_evidence_kinds=["endpoint"])
        )
        evidence = await evidence_service.ingest(_evidence())
        detection = _detection(evidence_ids=[evidence.record.evidence_id])

        first = await service.evaluate_detection(detection)
        second = await service.evaluate_detection(detection)

        assert len(first) == len(second) == 1
        decision = first[0]
        assert decision.decision_id == second[0].decision_id
        assert decision.policy_id == policy.policy_id
        assert decision.outcome == "decision_recorded"
        assert decision.decision_mode == "investigate"
        assert decision.evidence_ids == [evidence.record.evidence_id]
        assert decision.evidence_kinds == ["endpoint"]
        assert decision.requires_human_approval is True
        assert decision.automatic_enforcement is False
        assert len(await service._repository.list_decisions(TENANT_ID)) == 1
        assert await service._repository.list_decisions(OTHER_TENANT_ID) == []

        async with sessions() as session:
            row = await session.scalar(select(AutonomousDefenseDecisionRow))
            assert row is not None
            assert row.requires_human_approval is True
            row.outcome = "refused"
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()
            await session.rollback()
            await session.delete(row)
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_insufficient_evidence_refuses_even_when_detection_severity_is_critical():
    sessions, engine = await _sessions()
    try:
        service, _ = _service(sessions)
        await service._repository.upsert_policy(_policy(minimum_evidence_count=2, minimum_confidence=0.50))

        decisions = await service.evaluate_detection(_detection(severity="critical"))

        assert len(decisions) == 1
        assert decisions[0].outcome == "refused"
        assert decisions[0].containment_request_id is None
        assert any("minimum_evidence_count=2 not met" in reason for reason in decisions[0].reasons)
        assert decisions[0].automatic_enforcement is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_propose_containment_creates_approval_required_request_but_never_executes_adapter():
    sessions, engine = await _sessions()
    try:
        service, evidence_service = _service(sessions)
        await service._repository.upsert_policy(
            _policy(
                decision_mode="propose_containment",
                name="Propose endpoint isolation after corroborated evidence",
                minimum_confidence=0.80,
            )
        )
        evidence = await evidence_service.ingest(_evidence())
        decisions = await service.evaluate_detection(_detection(evidence_ids=[evidence.record.evidence_id]))

        assert len(decisions) == 1
        decision = decisions[0]
        assert decision.outcome == "containment_proposed"
        assert decision.containment_request_id is not None
        assert decision.requires_human_approval is True
        assert decision.automatic_enforcement is False
        async with sessions() as session:
            executions = (await session.scalars(select(ContainmentExecutionRow))).all()
            assert executions == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_observer_fails_closed_when_proposal_audit_configuration_is_missing():
    sessions, engine = await _sessions()
    try:
        service, evidence_service = _service(sessions, signing_key=None)
        await service._repository.upsert_policy(
            _policy(
                decision_mode="propose_containment",
                name="Audit-gated isolation proposal",
            )
        )
        evidence = await evidence_service.ingest(_evidence())

        assert await AutonomousDefenseObserver(service).observe(
            _detection(evidence_ids=[evidence.record.evidence_id])
        ) == []
        assert await service._repository.list_decisions(TENANT_ID) == []
    finally:
        await engine.dispose()


def test_autonomous_defense_routes_are_wired_without_an_execution_endpoint():
    from backend_api.soar_engine.app import app

    paths = {route.path for route in app.routes}
    assert "/api/soar/governed-containment/autonomous-defense/policies" in paths
    assert "/api/soar/governed-containment/autonomous-defense/decisions" in paths
    assert "/api/soar/governed-containment/autonomous-defense/evaluate" in paths
    assert "/api/soar/governed-containment/autonomous-defense/detections/{detection_id}/evaluate" in paths
    assert "/api/soar/governed-containment/defensive-data/sources" in paths
    assert "/api/soar/governed-containment/defensive-data/datasets" in paths
    assert "/api/soar/governed-containment/defensive-data/evaluation-policies" in paths
    assert "/api/soar/governed-containment/defensive-data/evaluations" in paths
    assert "/api/soar/governed-containment/defensive-data/advisory-assessments" in paths
    assert "/api/soar/governed-containment/telemetry-credentials" in paths
    assert "/api/soar/governed-containment/telemetry-credentials/{credential_id}/revoke" in paths
    assert not any("autonomous-defense" in path and "execute" in path for path in paths)
    assert not any("defensive-data" in path and any(term in path for term in ("execute", "enforce", "raw-telemetry", "train")) for path in paths)
    assert not any("telemetry-credentials" in path and any(term in path for term in ("execute", "enforce", "dispatch", "private-key")) for path in paths)
