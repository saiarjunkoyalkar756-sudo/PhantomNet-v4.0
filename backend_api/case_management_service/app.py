from backend_api.shared.service_factory import create_phantom_service
from pydantic import BaseModel
from loguru import logger
from typing import List, Optional
from datetime import datetime
from .database import create_cases_table, get_all_cases, get_case_by_id, create_case, update_case
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException

async def case_startup(app: FastAPI):
    # Ensure tables on startup
    create_cases_table()
    logger.info("Case Management Service: logic and DB initialized.")

app = create_phantom_service(
    name="Case Management Service",
    description="Service for tracking and managing security incidents and forensic cases.",
    version="1.0.0",
    custom_startup=case_startup
)

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

@app.post("/cases")
async def create_new_case(case_data: CaseCreate):
    case_id = create_case(case_data.model_dump())
    if case_id is None:
        raise HTTPException(status_code=500, detail="Failed to create case.")
    
    new_case = get_case_by_id(case_id)
    if new_case is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created case.")
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
