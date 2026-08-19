from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.governed_correlation import GovernedCorrelationEngine, GovernedCorrelationRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.evidence_vault.integration import EvidenceIntegrationService, IntegratedEvidenceRepository
from backend_api.shared.database import Base
from backend_api.threat_intelligence_service.world_intel_adapter import WorldIntelEnricher
from phantomnet_core.contracts import GovernedCorrelationRule, HostAssetRecord, IntegratedEvidenceRecord, IntegrityObservation


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


async def _isolated_evidence_service():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = IntegratedEvidenceRepository(sessions)
    return EvidenceIntegrationService(repository), repository, sessions, engine


def _identity_evidence(tenant_id: str = TENANT_ID) -> IntegratedEvidenceRecord:
    return IntegratedEvidenceRecord(
        evidence_id="evidence-phase4-identity-001",
        tenant_id=tenant_id,
        source_kind="identity",
        source_name="iam-baseline",
        source_record_id="identity-observation-001",
        observed_at=datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc),
        payload={"identity": {"principal": "analyst-1", "baseline_state": "review"}},
        tags=["identity", "baseline"],
        provenance={"adapter": "identity-observer", "read_only": True},
    )


@pytest.mark.asyncio
async def test_integrated_evidence_is_tenant_scoped_idempotent_and_projects_advisory_canonical_event():
    service, repository, _, engine = await _isolated_evidence_service()
    try:
        first = await service.ingest(_identity_evidence())
        duplicate = await service.ingest(_identity_evidence())

        assert first.created is True
        assert duplicate.created is False
        assert duplicate.record.evidence_id == first.record.evidence_id
        assert first.event.event_id == first.record.evidence_id
        assert first.event.event_type == "EVIDENCE.IDENTITY.OBSERVED"
        assert first.event.provenance["read_only"] is True
        assert first.event.payload["automatic_enforcement"] is False
        assert first.record.read_only is True
        assert first.record.automatic_enforcement is False
        assert len(first.record.payload_fingerprint()) == 64
        assert await repository.list_for_tenant(TENANT_ID, source_kind="identity") == [first.record]
        assert await repository.list_for_tenant(OTHER_TENANT_ID) == []
        with pytest.raises(LookupError):
            await repository.get_for_tenant(OTHER_TENANT_ID, first.record.evidence_id)
    finally:
        await engine.dispose()


def test_integrated_evidence_contract_rejects_writable_or_unattested_provenance():
    payload = _identity_evidence().model_dump()
    with pytest.raises(ValidationError, match="read-only"):
        IntegratedEvidenceRecord.model_validate({**payload, "read_only": False})
    with pytest.raises(ValidationError, match="automatic enforcement"):
        IntegratedEvidenceRecord.model_validate({**payload, "automatic_enforcement": True})
    with pytest.raises(ValidationError, match="provenance"):
        IntegratedEvidenceRecord.model_validate({**payload, "provenance": {"adapter": "identity-observer"}})


@pytest.mark.asyncio
async def test_endpoint_and_wazuh_evidence_integrate_without_changing_read_only_telemetry_or_response_boundaries():
    service, repository, sessions, engine = await _isolated_evidence_service()
    try:
        ingestion = EndpointTelemetryIngestion(
            EndpointInventoryRepository(sessions),
            evidence_integration=service,
        )
        asset = HostAssetRecord(
            asset_id="phase4-asset-001",
            tenant_id=TENANT_ID,
            agent_id="007",
            hostname="phase4-endpoint",
            platform="linux",
            source="wazuh",
            last_seen=datetime(2026, 8, 19, 12, 1, tzinfo=timezone.utc),
            evidence={"read_only": True},
        )
        asset_result = await ingestion.ingest_asset(asset)
        observation = IntegrityObservation(
            tenant_id=TENANT_ID,
            asset_id=asset.asset_id,
            agent_id="007",
            source_event_id="phase4-wazuh-integrity-001",
            source="wazuh",
            check_type="file",
            status="modified",
            severity="high",
            observed_at=datetime(2026, 8, 19, 12, 2, tzinfo=timezone.utc),
            path="/etc/passwd",
            evidence={"read_only": True},
        )
        integrity_result = await ingestion.ingest_integrity(observation)

        assert len(asset_result["events"]) == 1
        assert asset_result["integrated_evidence_created"] is True
        assert asset_result["integrated_evidence"].source_kind == "asset"
        assert len(integrity_result["events"]) == 1
        assert integrity_result["integrated_evidence_created"] is True
        assert integrity_result["integrated_evidence"].source_kind == "wazuh"
        stored = await repository.list_for_tenant(TENANT_ID)
        assert {record.source_kind for record in stored} == {"asset", "wazuh"}
        assert all(record.read_only and not record.automatic_enforcement for record in stored)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_successful_world_intel_context_can_be_integrated_but_unavailable_context_cannot():
    service, _, _, engine = await _isolated_evidence_service()
    try:
        enricher = WorldIntelEnricher(lambda tool, args: {"tool": tool, "indicator": args["indicator"], "risk": "contextual"})
        successful = enricher.enrich("198.51.100.5")
        outcome = await service.ingest_intelligence(TENANT_ID, successful)

        assert outcome.created is True
        assert outcome.record.source_kind == "intelligence"
        assert outcome.record.source_name == "world-intel-mcp"
        assert outcome.record.read_only is True
        assert outcome.event.payload["automatic_enforcement"] is False
        with pytest.raises(ValueError, match="successful read-only"):
            await service.ingest_intelligence(TENANT_ID, {"status": "unavailable", "evidence": None})
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_integrated_evidence_projects_into_canonical_governed_correlation_without_response_authority():
    service, _, sessions, engine = await _isolated_evidence_service()
    try:
        correlation_repository = GovernedCorrelationRepository(sessions)
        await correlation_repository.upsert(
            GovernedCorrelationRule(
                tenant_id=TENANT_ID,
                version="1.0.0",
                name="Read-only intelligence context observed",
                description="Correlate an explicitly read-only intelligence context record for analyst review.",
                event_types=["EVIDENCE.INTELLIGENCE.OBSERVED"],
                predicates=[{"field": "payload.evidence.source_kind", "operator": "equals", "value": "intelligence"}],
                severity="medium",
                mitre_techniques=["T1589"],
                mitre_tactics=["reconnaissance"],
                threshold=1,
                window_seconds=60,
            )
        )
        outcome = await service.ingest_intelligence(
            TENANT_ID,
            WorldIntelEnricher(lambda tool, args: {"indicator": args["indicator"], "tool": tool}).enrich("203.0.113.20"),
        )
        processor = CanonicalBrokerProcessor(
            DetectionRepository(sessions),
            evaluators=(),
            async_evaluators=(GovernedCorrelationEngine(correlation_repository).evaluate_event,),
        )
        result = await processor.process(outcome.event.model_dump(mode="json"))

        assert len(result.created_detection_ids) == 1
        assert result.persisted_detections[0].automatic_enforcement is False
        assert result.persisted_detections[0].evidence["correlation"]["rule_version"] == "1.0.0"
    finally:
        await engine.dispose()


def test_evidence_routes_are_tenant_authenticated_and_exclude_response_operations():
    from backend_api.endpoint_inventory_service.main import app

    paths = {route.path for route in app.routes}
    assert "/evidence" in paths
    assert "/evidence/{evidence_id}" in paths
    assert not any("contain" in path or "response" in path for path in paths if "evidence" in path)
