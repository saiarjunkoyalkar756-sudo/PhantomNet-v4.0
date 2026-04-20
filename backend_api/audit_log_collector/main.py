from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .database import get_db
from . import crud
import datetime

router = APIRouter()

app = create_phantom_service(
    name="Audit Log Collector",
    description="Centralized audit log collection and indexing service.",
    version="1.0.0"
)
app.include_router(router)

class AuditLogBase(BaseModel):
    raw_log_data: str = Field(..., example="User 'admin' logged in from 192.168.1.100")
    action: str = Field(..., example="login")
    timestamp: Optional[datetime.datetime] = None
    event_id: Optional[str] = None
    actor_id: Optional[str] = None
    resource: Optional[str] = None
    status: Optional[str] = None
    source_ip: Optional[str] = None
    host_identifier: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    ingested_at: datetime.datetime

    class Config:
        from_attributes = True

@router.post("/ingest/", status_code=status.HTTP_201_CREATED)
def ingest_single_audit_log(audit_log: AuditLogCreate, db: Session = Depends(get_db)):
    db_audit = crud.create_audit_log(db=db, **audit_log.dict())
    return success_response(data=db_audit)

@router.post("/ingest/batch", status_code=status.HTTP_201_CREATED)
def ingest_batch_audit_logs(audit_logs: List[AuditLogCreate], db: Session = Depends(get_db)):
    created_logs = []
    for audit_log in audit_logs:
        db_audit = crud.create_audit_log(db=db, **audit_log.dict())
        created_logs.append(db_audit)
    return success_response(data=created_logs)

@router.get("/logs/")
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    logs = crud.get_audit_logs(db=db, skip=skip, limit=limit, actor_id=actor_id, action=action)
    return success_response(data=logs)
