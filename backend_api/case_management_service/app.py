# backend_api/case_management_service/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Optional
from datetime import datetime

from .database import create_cases_table, get_all_cases, get_case_by_id, create_case, update_case

logger = logging.getLogger(__name__)

app = FastAPI()

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

class Case(CaseCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    timeline: List[dict]
    notes: List[dict]
    playbook_status: dict

    class Config:
        from_attributes = True


@app.on_event("startup")
async def startup_event():
    logger.info("Case Management Service starting up...")
    create_cases_table()

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Case Management Service is healthy"}

@app.post("/cases", response_model=Case)
async def create_new_case(case_data: CaseCreate):
    case_id = create_case(case_data.dict())
    if case_id is None:
        raise HTTPException(status_code=500, detail="Failed to create case.")
    
    new_case = get_case_by_id(case_id)
    if new_case is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve newly created case.")
    return Case(**new_case)

@app.get("/cases", response_model=List[Case])
async def get_all_incidents():
    cases = get_all_cases()
    return [Case(**c) for c in cases]

@app.get("/cases/{case_id}", response_model=Case)
async def get_incident_by_id(case_id: int):
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    return Case(**case)

@app.put("/cases/{case_id}", response_model=Case)
async def update_incident(case_id: int, updates: CaseUpdate):
    success = update_case(case_id, updates.dict(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update case.")
    
    updated_case = get_case_by_id(case_id)
    if updated_case is None:
        raise HTTPException(status_code=404, detail="Case not found after update.")
    return Case(**updated_case)

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
    return {"message": "Note added successfully."}

@app.post("/cases/{case_id}/execute_playbook")
async def execute_playbook_on_case(case_id: int, playbook_name: str):
    """
    Simulates execution of a playbook for a given case.
    """
    case = get_case_by_id(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    
    playbook_status = case.get("playbook_status", {})
    playbook_status[playbook_name] = {"status": "started", "timestamp": datetime.now().isoformat()}
    success = update_case(case_id, {"playbook_status": playbook_status})
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update playbook status.")
    
    return {"message": f"Playbook '{playbook_name}' execution simulated."}
