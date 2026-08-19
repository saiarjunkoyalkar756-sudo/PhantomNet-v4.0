"""FastAPI surface for governed analyst threat hunting and dashboard summaries."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from pydantic import BaseModel

from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from backend_api.shared.service_factory import create_phantom_service
from backend_api.threat_hunting_service.service import (
    HuntRequest,
    SavedHuntCreate,
    ThreatHuntingService,
    init_hunt_store,
)
from backend_api.core.response import success_response


async def hunt_startup(_app) -> None:
    await init_hunt_store()


app = create_phantom_service(
    name="Threat Hunting Service",
    description="Tenant-scoped structured threat hunting and SOC dashboard aggregation.",
    version="1.0.0",
    custom_startup=hunt_startup,
)
hunt_service = ThreatHuntingService()


class AutomatedHuntRequest(BaseModel):
    template: str


@app.post("/hunts/execute")
async def execute_hunt(
    request: HuntRequest,
    current_user: User = Depends(require_capability("alerts:read")),
):
    try:
        result = await hunt_service.hunt(str(current_user.tenant_id), request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=result)


@app.post("/hunts/saved", status_code=201)
async def create_saved_hunt(
    request: SavedHuntCreate,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        hunt = await hunt_service.create_saved_hunt(str(current_user.tenant_id), current_user.username, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=hunt.model_dump(mode="json"))


@app.get("/hunts/saved")
async def list_saved_hunts(current_user: User = Depends(require_capability("alerts:read"))):
    hunts = await hunt_service.list_saved_hunts(str(current_user.tenant_id))
    return success_response(data=[hunt.model_dump(mode="json") for hunt in hunts])


@app.post("/hunts/saved/{hunt_id}/execute")
async def execute_saved_hunt(
    hunt_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    try:
        result = await hunt_service.run_saved_hunt(str(current_user.tenant_id), hunt_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Saved hunt not found.") from exc
    return success_response(data=result)


@app.get("/hunts/automated")
async def run_automated_hunts(current_user: User = Depends(require_capability("alerts:read"))):
    results = await hunt_service.automated_hunts(str(current_user.tenant_id))
    return success_response(data=results)


@app.get("/analyst-context/alerts/{alert_id}")
async def analyst_alert_context(
    alert_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    """Return tenant-owned, explainable evidence-to-decision context for one alert; no response is proposed or dispatched."""
    try:
        context = await hunt_service.analyst_context_for_alert(str(current_user.tenant_id), alert_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Alert not found.") from exc
    return success_response(data=context)


@app.get("/analyst-context/cases/{case_id}")
async def analyst_case_context(
    case_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    """Return tenant-owned, explainable evidence-to-decision context for one case; no lifecycle state is changed."""
    try:
        context = await hunt_service.analyst_context_for_case(str(current_user.tenant_id), case_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Case not found.") from exc
    return success_response(data=context)


@app.get("/dashboard/summary")
async def dashboard_summary(current_user: User = Depends(require_capability("alerts:read"))):
    summary = await hunt_service.dashboard_summary(str(current_user.tenant_id))
    return success_response(data=summary)
