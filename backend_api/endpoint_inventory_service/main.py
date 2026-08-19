"""Endpoint inventory and integrity evidence API."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, Header, HTTPException, Query
from pydantic import BaseModel

from backend_api.core.response import success_response
from backend_api.endpoint_inventory_service.forwarders import (
    ForwarderAuthenticationError,
    ForwarderReplayError,
    WazuhForwarderService,
    init_forwarder_store,
)
from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository, init_endpoint_inventory_store
from backend_api.evidence_vault.integration import (
    EvidenceIntegrationService,
    EvidenceSourceKind,
    IntegratedEvidenceRepository,
    init_integrated_evidence_store,
)
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from backend_api.shared.service_factory import create_phantom_service
from phantomnet_core.contracts import HostAssetRecord, IntegratedEvidenceRecord, IntegrityObservation, WazuhTelemetryBatch


async def endpoint_inventory_startup(_app) -> None:
    await init_endpoint_inventory_store()
    await init_forwarder_store()
    await init_integrated_evidence_store()


app = create_phantom_service(
    name="Endpoint Inventory Service",
    description="Canonical endpoint asset inventory and read-only integrity evidence ingestion.",
    version="1.0.0",
    custom_startup=endpoint_inventory_startup,
)
repository = EndpointInventoryRepository()
evidence_repository = IntegratedEvidenceRepository()
evidence_integration = EvidenceIntegrationService(evidence_repository)
ingestion = EndpointTelemetryIngestion(repository, evidence_integration=evidence_integration)
forwarders = WazuhForwarderService(ingestion=ingestion)


class WazuhAlertRequest(BaseModel):
    alert: Dict[str, Any]


class WazuhForwarderRegistrationRequest(BaseModel):
    name: str


@app.post("/assets", status_code=201)
async def ingest_asset(
    asset: HostAssetRecord,
    current_user: User = Depends(require_capability("config:write")),
):
    if asset.tenant_id != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Endpoint asset tenant does not match authenticated tenant.")
    result = await ingestion.ingest_asset(asset)
    data = {
        "asset": result["asset"].model_dump(mode="json"),
        "created": result["created"],
        "events": [event.model_dump(mode="json") for event in result["events"]],
        "automatic_enforcement": False,
    }
    if "integrated_evidence" in result:
        data["integrated_evidence"] = result["integrated_evidence"].model_dump(mode="json")
        data["integrated_evidence_created"] = result["integrated_evidence_created"]
    return success_response(data=data)


@app.post("/integrity", status_code=201)
async def ingest_integrity(
    observation: IntegrityObservation,
    current_user: User = Depends(require_capability("config:write")),
):
    if observation.tenant_id != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Integrity evidence tenant does not match authenticated tenant.")
    try:
        result = await ingestion.ingest_integrity(observation)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Referenced endpoint asset was not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    data = {
        "observation": result["observation"].model_dump(mode="json"),
        "created": result["created"],
        "events": [event.model_dump(mode="json") for event in result["events"]],
        "automatic_enforcement": False,
    }
    if "integrated_evidence" in result:
        data["integrated_evidence"] = result["integrated_evidence"].model_dump(mode="json")
        data["integrated_evidence_created"] = result["integrated_evidence_created"]
    return success_response(data=data)


@app.post("/wazuh/alerts", status_code=201)
async def ingest_wazuh_alert(
    request: WazuhAlertRequest,
    current_user: User = Depends(require_capability("config:write")),
):
    """Ingest a Wazuh-compatible alert as read-only inventory and integrity evidence."""
    try:
        result = await ingestion.ingest_wazuh_alert(str(current_user.tenant_id), request.alert)
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    data = {
        "asset": result["asset"].model_dump(mode="json"),
        "asset_created": result["asset_created"],
        "events": [event.model_dump(mode="json") for event in result["events"]],
        "automatic_enforcement": False,
        "adapter_mode": "read_only",
    }
    if "asset_integrated_evidence" in result:
        data["asset_integrated_evidence"] = result["asset_integrated_evidence"].model_dump(mode="json")
        data["asset_integrated_evidence_created"] = result["asset_integrated_evidence_created"]
    if "observation" in result:
        data["observation"] = result["observation"].model_dump(mode="json")
        data["integrity_created"] = result["integrity_created"]
    if "integrity_integrated_evidence" in result:
        data["integrity_integrated_evidence"] = result["integrity_integrated_evidence"].model_dump(mode="json")
        data["integrity_integrated_evidence_created"] = result["integrity_integrated_evidence_created"]
    return success_response(data=data)


@app.post("/wazuh/forwarders", status_code=201)
async def register_wazuh_forwarder(
    request: WazuhForwarderRegistrationRequest,
    current_user: User = Depends(require_capability("config:write")),
):
    try:
        forwarder, token = await forwarders.register(str(current_user.tenant_id), request.name, current_user.username)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return success_response(
        data={
            "forwarder": forwarder.model_dump(mode="json"),
            "forwarder_token": token,
            "token_delivery": "shown_once",
            "adapter_mode": "read_only_streaming",
            "automatic_enforcement": False,
        }
    )


@app.get("/wazuh/forwarders")
async def list_wazuh_forwarders(current_user: User = Depends(require_capability("config:write"))):
    records = await forwarders.list_for_tenant(str(current_user.tenant_id))
    return success_response(data=[record.model_dump(mode="json") for record in records])


@app.delete("/wazuh/forwarders/{forwarder_id}")
async def revoke_wazuh_forwarder(
    forwarder_id: str,
    current_user: User = Depends(require_capability("config:write")),
):
    try:
        record = await forwarders.revoke(str(current_user.tenant_id), forwarder_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Forwarder not found.") from exc
    return success_response(data=record.model_dump(mode="json"))


@app.post("/wazuh/forwarders/{forwarder_id}/stream", status_code=202)
async def stream_wazuh_telemetry(
    forwarder_id: str,
    batch: WazuhTelemetryBatch,
    x_phantomnet_forwarder_token: str = Header(..., min_length=16),
):
    """Receive one authenticated live Wazuh telemetry batch for its registered tenant."""
    try:
        result = await forwarders.stream_batch(forwarder_id, x_phantomnet_forwarder_token, batch)
    except ForwarderAuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Forwarder authentication failed.") from exc
    except ForwarderReplayError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=result)


@app.post("/evidence", status_code=201)
async def ingest_integrated_evidence(
    record: IntegratedEvidenceRecord,
    current_user: User = Depends(require_capability("config:write")),
):
    """Persist tenant-owned read-only integration evidence; this route has no response capability."""
    if record.tenant_id != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Integrated evidence tenant does not match authenticated tenant.")
    outcome = await evidence_integration.ingest(record)
    return success_response(
        data={
            "evidence": outcome.record.model_dump(mode="json"),
            "created": outcome.created,
            "event": outcome.event.model_dump(mode="json"),
            "automatic_enforcement": False,
        }
    )


@app.get("/evidence")
async def list_integrated_evidence(
    source_kind: EvidenceSourceKind | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("alerts:read")),
):
    """List only the authenticated tenant's read-only asset, endpoint, Wazuh, identity, intelligence, or graph evidence."""
    records = await evidence_repository.list_for_tenant(str(current_user.tenant_id), source_kind=source_kind, limit=limit)
    return success_response(data=[record.model_dump(mode="json") for record in records])


@app.get("/evidence/{evidence_id}")
async def get_integrated_evidence(
    evidence_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    try:
        record = await evidence_repository.get_for_tenant(str(current_user.tenant_id), evidence_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Integrated evidence was not found.") from exc
    return success_response(data=record.model_dump(mode="json"))


@app.get("/assets")
async def list_assets(
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("alerts:read")),
):
    assets = await repository.list_assets(str(current_user.tenant_id), limit=limit)
    return success_response(data=[asset.model_dump(mode="json") for asset in assets])


@app.get("/assets/{asset_id}/integrity")
async def list_asset_integrity(
    asset_id: str,
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("alerts:read")),
):
    observations = await repository.list_integrity(str(current_user.tenant_id), asset_id=asset_id, limit=limit)
    return success_response(data=[observation.model_dump(mode="json") for observation in observations])
