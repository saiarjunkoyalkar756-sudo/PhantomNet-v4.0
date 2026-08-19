from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.governed_correlation import (
    GovernedCorrelationEngine,
    GovernedCorrelationRepository,
)
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.shared.database import Base
from phantomnet_core.contracts import (
    DetectionRecord,
    EventEnvelope,
    GovernedCorrelationRule,
    GovernedCorrelationRuleFixture,
)


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


async def _isolated_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = GovernedCorrelationRepository(sessions)
    return repository, GovernedCorrelationEngine(repository), sessions, engine


def _rule(tenant_id: str = TENANT_ID, threshold: int = 2) -> GovernedCorrelationRule:
    return GovernedCorrelationRule(
        tenant_id=tenant_id,
        version="1.0.0",
        name="Repeated privileged process start",
        description="Detect repeated governed process telemetry for the same host.",
        event_types=["process.start"],
        predicates=[{"field": "payload.process_name", "operator": "equals", "value": "admin-tool"}],
        severity="high",
        mitre_techniques=["T1059"],
        mitre_tactics=["execution"],
        correlation_key_fields=["payload.hostname"],
        threshold=threshold,
        window_seconds=300,
    )


def _event(event_id: str, timestamp: datetime, tenant_id: str = TENANT_ID) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id,
        tenant_id=tenant_id,
        timestamp=timestamp,
        source="endpoint-agent",
        event_type="process.start",
        severity="medium",
        correlation_id="governed-correlation-test",
        payload={"hostname": "app-01", "process_name": "admin-tool"},
    )


def test_governed_rule_contract_rejects_raw_query_fields_actions_and_invalid_predicates():
    with pytest.raises(ValidationError):
        GovernedCorrelationRule.model_validate({**_rule().model_dump(), "raw_query": "MATCH (n) RETURN n"})
    with pytest.raises(ValidationError):
        GovernedCorrelationRule.model_validate({**_rule().model_dump(), "action": "isolate_endpoint"})
    with pytest.raises(ValidationError):
        GovernedCorrelationRule.model_validate({**_rule().model_dump(), "predicates": [{"field": "payload.__class__", "operator": "equals", "value": "x"}]})
    with pytest.raises(ValidationError):
        GovernedCorrelationRule.model_validate({**_rule().model_dump(), "mitre_tactics": []})


@pytest.mark.asyncio
async def test_governed_correlation_stores_tenant_match_evidence_before_threshold_and_emits_mitre_detection_after_threshold():
    repository, engine_service, _, engine = await _isolated_engine()
    try:
        stored = await repository.upsert(_rule())
        now = datetime.now(timezone.utc)

        first = await engine_service.evaluate_event(_event("governed-event-1", now))
        second = await engine_service.evaluate_event(_event("governed-event-2", now + timedelta(seconds=30)))

        assert first == []
        assert len(second) == 1
        assert second[0].tenant_id == TENANT_ID
        assert second[0].automatic_enforcement is False
        assert second[0].mitre_evidence[0].technique_id == "T1059"
        assert second[0].evidence["correlation"]["match_count"] == 2
        assert second[0].evidence["correlation"]["threshold"] == 2

        quality = await repository.quality_summary(TENANT_ID)
        assert quality == [{
            "rule_id": stored.rule_id,
            "name": stored.name,
            "enabled": True,
            "severity": "high",
            "match_count": 2,
            "detection_count": 1,
            "last_matched_at": now + timedelta(seconds=30),
        }]
        assert await repository.list_rules(OTHER_TENANT_ID) == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_governed_correlation_rule_upsert_preserves_existing_rule_identity_and_tenant_boundary():
    repository, _, _, engine = await _isolated_engine()
    try:
        initial = await repository.upsert(_rule())
        updated_input = _rule()
        updated_input.version = "1.1.0"
        updated_input.description = "Updated advisory-only governed correlation definition."
        updated = await repository.upsert(updated_input)

        assert updated.rule_id == initial.rule_id
        assert updated.version == "1.1.0"
        assert len(await repository.list_rules(TENANT_ID)) == 1
        await repository.upsert(_rule(OTHER_TENANT_ID))
        assert len(await repository.list_rules(OTHER_TENANT_ID)) == 1
        assert len(await repository.list_rules(TENANT_ID)) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_canonical_broker_processor_runs_async_governed_correlation_and_replay_does_not_duplicate_alert_occurrences():
    correlation_repository, correlation_engine, sessions, engine = await _isolated_engine()
    try:
        await correlation_repository.upsert(_rule())
        detection_repository = DetectionRepository(sessions)
        workflow = AlertWorkflow(sessions)
        processor = CanonicalBrokerProcessor(
            detection_repository,
            evaluators=(),
            async_evaluators=(correlation_engine.evaluate_event,),
            alert_workflow=workflow,
        )
        now = datetime.now(timezone.utc)

        first = await processor.process(_event("broker-correlation-1", now).model_dump(mode="json"))
        second_payload = _event("broker-correlation-2", now + timedelta(seconds=10)).model_dump(mode="json")
        second = await processor.process(second_payload)
        replay = await processor.process(second_payload)

        assert first.persisted_detections == ()
        assert len(second.created_detection_ids) == 1
        assert len(second.alert_workflows) == 1
        assert replay.created_detection_ids == ()
        assert replay.duplicate_detection_ids == second.created_detection_ids
        assert len(replay.alert_workflows) == 1
        alerts = await workflow.list_for_tenant(TENANT_ID)
        assert len(alerts) == 1
        assert alerts[0].occurrence_count == 1
        assert alerts[0].detection_ids == list(second.created_detection_ids)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_governed_rule_versions_are_monotonic_immutable_and_reproducible():
    repository, _, _, engine = await _isolated_engine()
    try:
        initial = await repository.upsert(_rule())
        revisions = await repository.list_revisions(TENANT_ID, initial.rule_id)
        assert [revision["version"] for revision in revisions] == ["1.0.0"]
        assert revisions[0]["definition"]["rule_id"] == initial.rule_id
        assert len(revisions[0]["definition_fingerprint"]) == 64
        assert revisions[0]["automatic_enforcement"] is False

        changed_without_version = _rule()
        changed_without_version.description = "Changed definition without a reviewed version increment."
        with pytest.raises(ValueError, match="requires a higher version"):
            await repository.upsert(changed_without_version)

        updated = _rule()
        updated.version = "1.1.0"
        updated.description = "Reviewed deterministic revision with a new alert suppression boundary."
        updated.suppression_window_seconds = 30
        stored_update = await repository.upsert(updated)
        assert stored_update.rule_id == initial.rule_id
        assert stored_update.version == "1.1.0"
        assert stored_update.suppression_window_seconds == 30
        assert [revision["version"] for revision in await repository.list_revisions(TENANT_ID, initial.rule_id)] == ["1.0.0", "1.1.0"]

        downgraded = _rule()
        downgraded.version = "1.0.1"
        with pytest.raises(ValueError, match="cannot be decreased"):
            await repository.upsert(downgraded)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_governed_rule_fixture_is_deterministic_read_only_and_tenant_bound():
    repository, _, _, engine = await _isolated_engine()
    try:
        stored = await repository.upsert(_rule(threshold=2))
        now = datetime.now(timezone.utc)
        fixture = GovernedCorrelationRuleFixture(
            fixture_id="fixture-governed-correlation-001",
            tenant_id=TENANT_ID,
            rule_id=stored.rule_id,
            events=[
                _event("fixture-event-later", now + timedelta(seconds=20)),
                _event("fixture-event-earlier", now),
            ],
            expected_detection_event_ids=["fixture-event-later"],
        )
        first = await repository.evaluate_fixture(TENANT_ID, stored.rule_id, fixture)
        second = await repository.evaluate_fixture(TENANT_ID, stored.rule_id, fixture)

        assert first == second
        assert first.evaluated_event_ids == ["fixture-event-earlier", "fixture-event-later"]
        assert first.matched_event_ids == ["fixture-event-earlier", "fixture-event-later"]
        assert first.detection_event_ids == ["fixture-event-later"]
        assert first.expectations_met is True
        assert first.automatic_enforcement is False
        quality = await repository.quality_summary(TENANT_ID)
        assert quality[0]["match_count"] == 0
        coverage = await repository.mitre_coverage_summary(TENANT_ID)
        assert coverage["technique_coverage"] == {"T1059": 1}
        assert coverage["tactic_coverage"] == {"execution": 1}
        assert coverage["automatic_enforcement"] is False

        with pytest.raises(ValueError, match="fixture tenant"):
            GovernedCorrelationRuleFixture(
                tenant_id=TENANT_ID,
                rule_id=stored.rule_id,
                events=[_event("cross-tenant-fixture", now, OTHER_TENANT_ID)],
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_rule_provided_alert_suppression_window_remains_bounded_and_advisory():
    _, _, sessions, engine = await _isolated_engine()
    try:
        workflow = AlertWorkflow(sessions, suppression_window_seconds=900)
        now = datetime.now(timezone.utc)
        base = {
            "tenant_id": TENANT_ID,
            "rule_id": "fixture-rule-suppression",
            "rule_version": "1.0.0",
            "correlation_id": "suppression-correlation",
            "severity": "high",
            "title": "Fixture suppression control",
            "evidence": {"alert_suppression_window_seconds": 30},
            "automatic_enforcement": False,
        }
        first = await workflow.ingest_detection(DetectionRecord(
            detection_id="suppression-detection-1",
            event_id="suppression-event-1",
            detected_at=now,
            **base,
        ))
        after_window = await workflow.ingest_detection(DetectionRecord(
            detection_id="suppression-detection-2",
            event_id="suppression-event-2",
            detected_at=now + timedelta(seconds=31),
            **base,
        ))

        assert first.created is True and first.suppressed is False
        assert after_window.created is True and after_window.suppressed is False
        assert first.alert.evidence["suppression_window_seconds"] == 30
    finally:
        await engine.dispose()


def test_governed_correlation_routes_are_wired_without_response_endpoints():
    from backend_api.correlation_engine.app import app

    paths = {route.path for route in app.routes}
    assert "/governed-rules" in paths
    assert "/governed-rules/quality" in paths
    assert "/governed-rules/mitre-coverage" in paths
    assert "/governed-rules/{rule_id}/revisions" in paths
    assert "/governed-rules/{rule_id}/fixtures/evaluate" in paths
    assert not any("contain" in path or "response" in path for path in paths if "governed-rules" in path)
