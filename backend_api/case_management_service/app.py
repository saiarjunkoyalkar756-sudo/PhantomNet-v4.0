from backend_api.shared.service_factory import create_phantom_service
from pydantic import BaseModel
from loguru import logger
from backend_api.shared.file_logging import get_rotating_file_logger
incident_logger = get_rotating_file_logger("incident_response", "incident_response.log")
from typing import List, Optional
from datetime import datetime
from .database import create_cases_table, get_all_cases, get_case_by_id, create_case, update_case
from backend_api.core.response import success_response, error_response
from backend_api.case_management_service.workflow import CaseWorkflow, init_case_workflow_store
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from fastapi import Depends, FastAPI, HTTPException

async def case_startup(app: FastAPI):
    # Ensure tables on startup
    create_cases_table()
    await init_case_workflow_store()
    logger.info("Case Management Service: logic and DB initialized.")

case_workflow = CaseWorkflow()

app = create_phantom_service(
    name="Case Management Service",
    description="Service for tracking and managing security incidents and forensic cases.",
    version="1.0.0",
    custom_startup=case_startup
)

class GovernedCaseTransition(BaseModel):
    status: str


class PlaybookRequest(BaseModel):
    playbook_id: str
    playbook_version: str


class PlaybookCompletion(BaseModel):
    status: str


class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str # e.g., low, medium, high, critical
    assigned_to: Optional[str] = None

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[List[dict]] = None
    timeline: Optional[List[dict]] = None
    playbook_status: Optional[dict] = None

class Case(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    severity: str
    assigned_to: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    timeline: List[dict]
    notes: List[dict]
    playbook_status: dict

    class Config:
        from_attributes = True

@app.post("/governed-cases/from-alert/{alert_id}", status_code=201)
async def create_governed_case_from_alert(
    alert_id: str,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        case, created = await case_workflow.create_from_alert(
            str(current_user.tenant_id), alert_id, current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Alert not found.", status_code=404)
    return success_response(data={"case": case.model_dump(mode="json"), "created": created})


@app.get("/governed-cases/{case_id}")
async def get_governed_case(
    case_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    try:
        case = await case_workflow.get_case(str(current_user.tenant_id), case_id)
    except LookupError:
        return error_response(code="NOT_FOUND", message="Case not found.", status_code=404)
    return success_response(data=case.model_dump(mode="json"))


@app.patch("/governed-cases/{case_id}/status")
async def transition_governed_case(
    case_id: str,
    transition: GovernedCaseTransition,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        case = await case_workflow.transition_case(
            str(current_user.tenant_id), case_id, transition.status, current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Case not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_CASE_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=case.model_dump(mode="json"))


@app.post("/governed-cases/{case_id}/playbooks", status_code=201)
async def request_case_playbook(
    case_id: str,
    request: PlaybookRequest,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        run = await case_workflow.request_playbook(
            tenant_id=str(current_user.tenant_id),
            case_id=case_id,
            playbook_id=request.playbook_id,
            playbook_version=request.playbook_version,
            actor=current_user.username,
            requires_approval=True,
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Case not found.", status_code=404)
    return success_response(data=run.model_dump(mode="json"))


@app.post("/governed-cases/playbook-runs/{run_id}/approve")
async def approve_case_playbook(
    run_id: str,
    current_user: User = Depends(require_capability("response:approve")),
):
    try:
        run = await case_workflow.transition_playbook(
            str(current_user.tenant_id), run_id, "approved", current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Playbook run not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_PLAYBOOK_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=run.model_dump(mode="json"))


@app.post("/governed-cases/playbook-runs/{run_id}/start")
async def start_case_playbook(
    run_id: str,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        run = await case_workflow.transition_playbook(
            str(current_user.tenant_id), run_id, "running", current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Playbook run not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_PLAYBOOK_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=run.model_dump(mode="json"))


@app.post("/governed-cases/playbook-runs/{run_id}/complete")
async def complete_case_playbook(
    run_id: str,
    completion: PlaybookCompletion,
    current_user: User = Depends(require_capability("cases:write")),
):
    if completion.status not in {"completed", "failed", "cancelled"}:
        return error_response(code="INVALID_PLAYBOOK_OUTCOME", message="Outcome must be completed, failed, or cancelled.", status_code=400)
    try:
        run = await case_workflow.transition_playbook(
            str(current_user.tenant_id), run_id, completion.status, current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Playbook run not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_PLAYBOOK_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=run.model_dump(mode="json"))


@app.get("/governed-cases/{case_id}/playbook-runs")
async def list_case_playbooks(
    case_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    runs = await case_workflow.list_playbook_runs(str(current_user.tenant_id), case_id)
    return success_response(data=[run.model_dump(mode="json") for run in runs])


@app.post("/cases")
async def create_new_case(case_data: CaseCreate):
    case_id = create_case(case_data.model_dump())
    if case_id is None:
        raise HTTPException(status_code=500, detail="Failed to create case.")
    
    new_case = get_case_by_id(case_id)
    if new_case is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created case.")
        
    try:
        incident_logger.info(
            f"Incident created - Case ID: {case_id}, Title: {case_data.title}, "
            f"Severity: {case_data.severity}, Assigned To: {case_data.assigned_to or 'Unassigned'}, "
            f"Status: open"
        )
    except Exception as log_err:
        logger.error(f"Error writing to incident_response.log: {log_err}")
        
    return success_response(data=Case(**new_case).model_dump())

@app.get("/cases")
async def get_all_incidents():
    cases = get_all_cases()
    return success_response(data=[Case(**c).model_dump() for c in cases])

@app.get("/cases/{case_id}")
async def get_incident_by_id(case_id: int):
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return success_response(data=Case(**case).model_dump())

@app.put("/cases/{case_id}")
async def update_incident(case_id: int, updates: CaseUpdate):
    success = update_case(case_id, updates.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update case.")
    
    updated_case = get_case_by_id(case_id)
    if updated_case is None:
        raise HTTPException(status_code=404, detail="Case not found after update.")
        
    try:
        status_change = updates.status or "no_change"
        assigned_change = updates.assigned_to or "no_change"
        incident_logger.info(
            f"Incident status change - Case ID: {case_id}, Status Update: {status_change}, "
            f"Assigned To Update: {assigned_change}"
        )
    except Exception as log_err:
        logger.error(f"Error writing to incident_response.log: {log_err}")
        
    return success_response(data=Case(**updated_case).model_dump())

@app.post("/cases/{case_id}/add_note")
async def add_note_to_case(case_id: int, note: str):
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    
    notes = case.get("notes", [])
    notes.append({"timestamp": datetime.now().isoformat(), "note": note})
    success = update_case(case_id, {"notes": notes})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add note.")
    return success_response(data={"message": "Note added successfully."})

@app.post("/cases/{case_id}/execute_playbook")
async def execute_playbook_on_case(case_id: int, playbook_name: str):
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    
    playbook_status = case.get("playbook_status", {})
    playbook_status[playbook_name] = {"status": "started", "timestamp": datetime.now().isoformat()}
    success = update_case(case_id, {"playbook_status": playbook_status})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update playbook status.")
    
    return success_response(data={"message": f"Playbook '{playbook_name}' execution simulated."})
