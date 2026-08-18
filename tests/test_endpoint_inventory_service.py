import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.endpoint_inventory_service.wazuh_adapter import WazuhReadOnlyAdapter
from backend_api.shared.database import Base
from backend_api.threat_hunting_service.service import HuntFilter, HuntRequest, ThreatHuntingService
from phantomnet_core.contracts import HostAssetRecord, IntegrityObservation


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


async def _isolated_endpoint_services():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = EndpointInventoryRepository(sessions)
    return repository, EndpointTelemetryIngestion(repository), engine


def _asset(tenant_id=TENANT_ID) -> HostAssetRecord:
    return HostAssetRecord(
        tenant_id=tenant_id,
        agent_id="agent-001",
        hostname="srv-001",
        platform="linux",
        os_version="Ubuntu 24.04",
        ip_addresses=["10.0.0.10"],
        software=[{"name": "openssh-server", "version": "9.6"}],
        tags=["production"],
        source="phantomnet-agent",
        evidence={"collector": "software_collector"},
    )


@pytest.mark.asyncio
async def test_asset_inventory_upserts_per_tenant_agent_and_emits_canonical_event():
    repository, ingestion, engine = await _isolated_endpoint_services()
    try:
        first = await ingestion.ingest_asset(_asset())
        updated_input = _asset()
        updated_input.hostname = "srv-001-renamed"
        second = await ingestion.ingest_asset(updated_input)

        assert first["created"] is True
        assert second["created"] is False
        assert second["asset"].asset_id == first["asset"].asset_id
        assert second["asset"].hostname == "srv-001-renamed"
        assert second["events"][0].event_type == "HOST_INVENTORY"
        assert second["events"][0].payload["automatic_enforcement"] is False
        assert len(await repository.list_assets(TENANT_ID)) == 1
        assert await repository.list_assets(OTHER_TENANT_ID) == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_integrity_evidence_is_idempotent_tenant_scoped_and_refuses_auto_enforcement():
    repository, ingestion, engine = await _isolated_endpoint_services()
    try:
        asset = (await ingestion.ingest_asset(_asset()))["asset"]
        observation = IntegrityObservation(
            tenant_id=TENANT_ID,
            asset_id=asset.asset_id,
            agent_id=asset.agent_id,
            source_event_id="agent-event-001",
            source="phantomnet-agent",
            check_type="file",
            status="modified",
            severity="high",
            path="/etc/ssh/sshd_config",
            observed_hash="new-hash",
            expected_hash="old-hash",
            evidence={"collector": "self_monitor"},
        )
        first = await ingestion.ingest_integrity(observation)
        retry = await ingestion.ingest_integrity(observation)

        assert first["created"] is True
        assert retry["created"] is False
        assert first["events"][0].event_type == "HOST_INTEGRITY"
        assert first["events"][0].severity == "high"
        assert (await repository.list_integrity(TENANT_ID, asset.asset_id))[0].automatic_enforcement is False
        assert await repository.list_integrity(OTHER_TENANT_ID) == []

        with pytest.raises(ValueError, match="never permits automatic enforcement"):
            await repository.persist_integrity(observation.model_copy(update={"automatic_enforcement": True}))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_wazuh_adapter_normalizes_read_only_syscheck_evidence_and_refuses_containment():
    _repository, ingestion, engine = await _isolated_endpoint_services()
    adapter = WazuhReadOnlyAdapter()
    wazuh_alert = {
        "id": "wazuh-alert-001",
        "timestamp": "2026-08-18T15:30:00Z",
        "agent": {"id": "007", "name": "wazuh-host", "ip": "10.0.0.20", "os": {"name": "Ubuntu", "version": "24.04"}},
        "rule": {"id": "550", "level": 10, "description": "Integrity checksum changed", "groups": ["syscheck", "integrity"]},
        "syscheck": {"event": "modified", "path": "/etc/passwd", "sha256_before": "before", "sha256_after": "after"},
    }
    try:
        result = await ingestion.ingest_wazuh_alert(TENANT_ID, wazuh_alert)
        retry = await ingestion.ingest_wazuh_alert(TENANT_ID, wazuh_alert)

        assert result["asset"].source == "wazuh"
        assert result["observation"].status == "modified"
        assert result["observation"].severity == "high"
        assert result["observation"].automatic_enforcement is False
        assert [event.event_type for event in result["events"]] == ["HOST_INVENTORY", "HOST_INTEGRITY"]
        assert retry["integrity_created"] is False
        hunt_service = ThreatHuntingService(_repository._session_factory)
        asset_hunt = await hunt_service.hunt(
            TENANT_ID, HuntRequest(dataset="assets", filters=[HuntFilter(field="hostname", operator="contains", value="wazuh")])
        )
        integrity_hunt = await hunt_service.hunt(
            TENANT_ID, HuntRequest(dataset="integrity", filters=[HuntFilter(field="status", operator="eq", value="modified")])
        )
        assert asset_hunt["result_count"] == 1
        assert integrity_hunt["results"][0]["path"] == "/etc/passwd"
        with pytest.raises(PermissionError, match="read-only"):
            await adapter.request_containment("block")
    finally:
        await engine.dispose()
