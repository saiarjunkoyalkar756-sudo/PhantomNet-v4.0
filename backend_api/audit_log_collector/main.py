from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime

from . import crud, models
from .database import SessionLocal, engine, get_db



router = APIRouter()

# Pydantic models for API request/response validation
from pydantic import BaseModel, Field

class AuditLogBase(BaseModel):
    raw_log_data: str = Field(..., example="User 'admin' logged in from 192.168.1.100")
    action: str = Field(..., example="login", description="The action performed (e.g., 'login', 'file_access', 'config_change').")
    timestamp: Optional[datetime.datetime] = Field(None, description="Timestamp of the audit event. Defaults to server ingestion time.")
    event_id: Optional[str] = Field(None, example="4624", description="Event ID from the source system (e.g., Windows Event ID).")
    actor_id: Optional[str] = Field(None, example="admin", description="Identifier of the user or process performing the action.")
    resource: Optional[str] = Field(None, example="/var/log/syslog", description="The resource affected by the action.")
    status: Optional[str] = Field(None, example="success", description="Outcome of the action ('success' or 'failure').")
    source_ip: Optional[str] = Field(None, example="192.168.1.100", description="Source IP address related to the action.")
    host_identifier: Optional[str] = Field(None, example="server-prod-01", description="Host where the audit event occurred.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured metadata from the audit event.")

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    ingested_at: datetime.datetime

    class Config:
        orm_mode = True

@router.post("/ingest/", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
def ingest_single_audit_log(audit_log: AuditLogCreate, db: Session = Depends(get_db)):
    """
    Ingest a single audit log event into the collector.
    """
    db_audit = crud.create_audit_log(
        db=db,
        raw_log_data=audit_log.raw_log_data,
        action=audit_log.action,
        timestamp=audit_log.timestamp,
        event_id=audit_log.event_id,
        actor_id=audit_log.actor_id,
        resource=audit_log.resource,
        status=audit_log.status,
        source_ip=audit_log.source_ip,
        host_identifier=audit_log.host_identifier,
        metadata=audit_log.metadata
    )
    return db_audit

@router.post("/ingest/batch", response_model=List[AuditLogResponse], status_code=status.HTTP_201_CREATED)
def ingest_batch_audit_logs(audit_logs: List[AuditLogCreate], db: Session = Depends(get_db)):
    """
    Ingest multiple audit log events into the collector in a single batch.
    """
    created_logs = []
    for audit_log in audit_logs:
        db_audit = crud.create_audit_log(
            db=db,
            raw_log_data=audit_log.raw_log_data,
            action=audit_log.action,
            timestamp=audit_log.timestamp,
            event_id=audit_log.event_id,
            actor_id=audit_log.actor_id,
            resource=audit_log.resource,
            status=audit_log.status,
            source_ip=audit_log.source_ip,
            host_identifier=audit_log.host_identifier,
            metadata=audit_log.metadata
        )
        created_logs.append(db_audit)
    return created_logs

@router.get("/logs/", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    host_identifier: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve audit log events with optional filters.
    """
    logs = crud.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        start_time=start_time,
        end_time=end_time,
        actor_id=actor_id,
        action=action,
        resource=resource,
        host_identifier=host_identifier,
        status_filter=status_filter
    )
    return logs
