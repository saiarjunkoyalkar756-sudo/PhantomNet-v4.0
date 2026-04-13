from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from . import crud, playbook_model
from .database import SessionLocal, engine, get_db



router = APIRouter()

# Pydantic models for API request/response validation
from pydantic import BaseModel, Field
import datetime

class PlaybookBase(BaseModel):
    name: str = Field(..., example="isolate_infected_host")
    description: Optional[str] = Field(None, example="Automated response to isolate a host detected with malware.")
    steps: List[Dict[str, Any]] = Field(..., example=[{"action": "get_host_info", "parameters": {"host_id": "123"}}, {"action": "isolate_host", "parameters": {"host_id": "123"}}])
    tags: Optional[str] = Field(None, example="malware, incident_response")

class PlaybookCreate(PlaybookBase):
    pass

class PlaybookUpdate(PlaybookBase):
    name: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    is_ai_generated: Optional[bool] = None
    approved_by_human: Optional[bool] = None

class PlaybookResponse(PlaybookBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: str
    is_ai_generated: bool
    approved_by_human: bool
    version: int

    class Config:
        orm_mode = True
        
class PlaybookRunBase(BaseModel):
    playbook_id: int
    triggered_by: Optional[str] = None

class PlaybookRunCreate(PlaybookRunBase):
    pass

class PlaybookRunUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime.datetime] = None

class PlaybookRunResponse(PlaybookRunBase):
    id: int
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    status: str
    result: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class PlaybookApprovalBase(BaseModel):
    playbook_run_id: int
    approver_id: str
    approved: bool
    approval_notes: Optional[str] = None

class PlaybookApprovalCreate(PlaybookApprovalBase):
    pass

class PlaybookApprovalResponse(PlaybookApprovalBase):
    id: int
    approved_at: datetime.datetime

    class Config:
        orm_mode = True


@router.post("/playbooks/", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
def create_new_playbook(playbook: PlaybookCreate, db: Session = Depends(get_db)):
    db_playbook = crud.get_playbook(db, name=playbook.name)
    if db_playbook:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Playbook with this name already exists")
    return crud.create_playbook(db=db, **playbook.dict())

@router.get("/playbooks/", response_model=List[PlaybookResponse])
def read_playbooks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    playbooks = crud.get_playbooks(db, skip=skip, limit=limit)
    return playbooks

@router.get("/playbooks/{playbook_id}", response_model=PlaybookResponse)
def read_playbook(playbook_id: int, db: Session = Depends(get_db)):
    db_playbook = crud.get_playbook(db, playbook_id=playbook_id)
    if db_playbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return db_playbook

@router.put("/playbooks/{playbook_id}", response_model=PlaybookResponse)
def update_existing_playbook(playbook_id: int, playbook: PlaybookUpdate, db: Session = Depends(get_db)):
    db_playbook = crud.update_playbook(db=db, playbook_id=playbook_id, **playbook.dict(exclude_unset=True))
    if db_playbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return db_playbook

@router.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_playbook(playbook_id: int, db: Session = Depends(get_db)):
    if not crud.delete_playbook(db=db, playbook_id=playbook_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return {"message": "Playbook deleted successfully"}

@router.post("/playbooks/{playbook_id}/run", response_model=PlaybookRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_playbook_run(playbook_id: int, triggered_by: Optional[str] = None, db: Session = Depends(get_db)):
    db_playbook = crud.get_playbook(db, playbook_id=playbook_id)
    if db_playbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    
    # In a real scenario, this would trigger an asynchronous execution process
    # For now, we just record the run
    return crud.create_playbook_run(db=db, playbook_id=playbook_id, triggered_by=triggered_by)

@router.get("/playbook_runs/", response_model=List[PlaybookRunResponse])
def read_playbook_runs(playbook_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    runs = crud.get_playbook_runs(db, playbook_id=playbook_id, skip=skip, limit=limit)
    return runs

@router.get("/playbook_runs/{run_id}", response_model=PlaybookRunResponse)
def read_playbook_run(run_id: int, db: Session = Depends(get_db)):
    db_run = crud.get_playbook_run(db, run_id=run_id)
    if db_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook run not found")
    return db_run

@router.put("/playbook_runs/{run_id}", response_model=PlaybookRunResponse)
def update_playbook_run_status(run_id: int, run_update: PlaybookRunUpdate, db: Session = Depends(get_db)):
    db_run = crud.update_playbook_run(db=db, run_id=run_id, **run_update.dict(exclude_unset=True))
    if db_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook run not found")
    return db_run

@router.post("/playbook_approvals/", response_model=PlaybookApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_playbook_approval_record(approval: PlaybookApprovalCreate, db: Session = Depends(get_db)):
    db_run = crud.get_playbook_run(db, run_id=approval.playbook_run_id)
    if db_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook run not found")
    
    return crud.create_playbook_approval(db=db, **approval.dict())
