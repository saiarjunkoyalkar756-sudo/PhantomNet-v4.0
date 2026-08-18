"""Canonical endpoint telemetry ingestion bridge for native agents and Wazuh-compatible payloads."""

from __future__ import annotations

from typing import Any, Mapping

from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.endpoint_inventory_service.wazuh_adapter import WazuhReadOnlyAdapter
from phantomnet_core.contracts import EventEnvelope, HostAssetRecord, IntegrityObservation


class EndpointTelemetryIngestion:
    """Persist endpoint evidence and return canonical events without invoking response actions."""

    def __init__(
        self,
        repository: EndpointInventoryRepository | None = None,
        wazuh_adapter: WazuhReadOnlyAdapter | None = None,
    ):
        self.repository = repository or EndpointInventoryRepository()
        self.wazuh_adapter = wazuh_adapter or WazuhReadOnlyAdapter()

    @staticmethod
    def _asset_event(asset: HostAssetRecord) -> EventEnvelope:
        return EventEnvelope(
            tenant_id=asset.tenant_id,
            source=asset.source,
            event_type="HOST_INVENTORY",
            severity="informational",
            payload={"asset": asset.model_dump(mode="json"), "automatic_enforcement": False},
            tags=["endpoint", "inventory", asset.source],
            provenance={"adapter": asset.source, "read_only": asset.source == "wazuh"},
        )

    @staticmethod
    def _integrity_event(observation: IntegrityObservation) -> EventEnvelope:
        return EventEnvelope(
            event_id=observation.source_event_id,
            timestamp=observation.observed_at,
            tenant_id=observation.tenant_id,
            source=observation.source,
            event_type="HOST_INTEGRITY",
            severity=observation.severity,
            payload={"integrity": observation.model_dump(mode="json"), "automatic_enforcement": False},
            tags=["endpoint", "integrity", observation.check_type, observation.source],
            provenance={"adapter": observation.source, "read_only": observation.source == "wazuh"},
        )

    async def ingest_asset(self, asset: HostAssetRecord) -> dict[str, Any]:
        persisted, created = await self.repository.upsert_asset(asset)
        return {"asset": persisted, "created": created, "events": (self._asset_event(persisted),)}

    async def ingest_integrity(self, observation: IntegrityObservation) -> dict[str, Any]:
        persisted, created = await self.repository.persist_integrity(observation)
        return {"observation": persisted, "created": created, "events": (self._integrity_event(persisted),)}

    async def ingest_wazuh_alert(self, tenant_id: str, alert: Mapping[str, Any]) -> dict[str, Any]:
        asset, observation = self.wazuh_adapter.normalize(tenant_id, alert)
        asset_result = await self.ingest_asset(asset)
        events = list(asset_result["events"])
        result: dict[str, Any] = {"asset": asset_result["asset"], "asset_created": asset_result["created"], "events": events}
        if observation is not None:
            observation = observation.model_copy(update={"asset_id": asset_result["asset"].asset_id})
            integrity_result = await self.ingest_integrity(observation)
            result.update(
                {
                    "observation": integrity_result["observation"],
                    "integrity_created": integrity_result["created"],
                }
            )
            result["events"].extend(integrity_result["events"])
        result["automatic_enforcement"] = False
        return result
