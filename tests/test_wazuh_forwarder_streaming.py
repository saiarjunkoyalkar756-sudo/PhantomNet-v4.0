import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.endpoint_inventory_service.forwarders import (
    ForwarderAuthenticationError,
    ForwarderReplayError,
    WazuhForwarderService,
)
from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.shared.database import Base
from phantomnet_core.contracts import WazuhTelemetryBatch


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


def _wazuh_alert(alert_id: str = "wazuh-live-001"):
    return {
        "id": alert_id,
        "timestamp": "2026-08-18T16:00:00Z",
        "agent": {"id": "007", "name": "streamed-host", "ip": "10.0.0.20", "os": {"name": "Ubuntu", "version": "24.04"}},
        "rule": {"id": "550", "level": 10, "description": "Integrity checksum changed", "groups": ["syscheck"]},
        "syscheck": {"event": "modified", "path": "/etc/passwd", "sha256_before": "before", "sha256_after": "after"},
    }


async def _isolated_forwarder_service():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    repository = EndpointInventoryRepository(sessions)
    ingestion = EndpointTelemetryIngestion(repository)
    return WazuhForwarderService(sessions, ingestion), repository, engine


@pytest.mark.asyncio
async def test_registered_forwarder_streams_tenant_bound_live_batch_once_and_returns_no_response_actions():
    service, repository, engine = await _isolated_forwarder_service()
    try:
        forwarder, token = await service.register(TENANT_ID, "wazuh-prod-a", "admin-1")
        result = await service.stream_batch(
            forwarder.forwarder_id,
            token,
            WazuhTelemetryBatch(batch_id="batch-0001", sequence=1, alerts=[_wazuh_alert()]),
        )

        assert result["sequence"] == 1
        assert result["asset_created"] == 1
        assert result["integrity_created"] == 1
        assert result["canonical_event_count"] == 2
        assert result["automatic_enforcement"] is False
        assert result["adapter_mode"] == "read_only_streaming"
        listed = await service.list_for_tenant(TENANT_ID)
        assert listed[0].last_sequence == 1
        assert listed[0].last_seen_at is not None
        assert await service.list_for_tenant(OTHER_TENANT_ID) == []
        assert len(await repository.list_assets(TENANT_ID)) == 1
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_forwarder_stream_refuses_invalid_token_replay_and_out_of_order_sequences():
    service, _repository, engine = await _isolated_forwarder_service()
    try:
        forwarder, token = await service.register(TENANT_ID, "wazuh-prod-b", "admin-1")
        batch = WazuhTelemetryBatch(batch_id="batch-0002", sequence=1, alerts=[_wazuh_alert("wazuh-live-002")])
        with pytest.raises(ForwarderAuthenticationError):
            await service.stream_batch(forwarder.forwarder_id, "invalid-token-value", batch)
        await service.stream_batch(forwarder.forwarder_id, token, batch)
        with pytest.raises(ForwarderReplayError, match="already accepted"):
            await service.stream_batch(forwarder.forwarder_id, token, batch)
        with pytest.raises(ForwarderReplayError, match="must be 2"):
            await service.stream_batch(
                forwarder.forwarder_id,
                token,
                WazuhTelemetryBatch(batch_id="batch-0003", sequence=3, alerts=[_wazuh_alert("wazuh-live-003")]),
            )
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_revoked_forwarder_and_streaming_service_refuse_further_telemetry_or_containment():
    service, _repository, engine = await _isolated_forwarder_service()
    try:
        forwarder, token = await service.register(TENANT_ID, "wazuh-prod-c", "admin-1")
        revoked = await service.revoke(TENANT_ID, forwarder.forwarder_id)

        assert revoked.status == "revoked"
        with pytest.raises(ForwarderAuthenticationError):
            await service.stream_batch(
                forwarder.forwarder_id,
                token,
                WazuhTelemetryBatch(batch_id="batch-0004", sequence=1, alerts=[_wazuh_alert("wazuh-live-004")]),
            )
        with pytest.raises(LookupError):
            await service.revoke(OTHER_TENANT_ID, forwarder.forwarder_id)
        with pytest.raises(PermissionError, match="telemetry-only"):
            await service.request_containment("block")
    finally:
        await engine.dispose()
