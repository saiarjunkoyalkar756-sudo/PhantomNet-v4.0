from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime

from . import crud, models
from .database import SessionLocal, engine, get_db



router = APIRouter()

# Pydantic models for API request/response validation
from pydantic import BaseModel, Field

class RawLogEventBase(BaseModel):
    raw_log_data: str = Field(..., example="<13>Jan 1 00:00:00 hostname program: Message content")
    source_type: str = Field(..., example="syslog", description="Type of log source (e.g., 'syslog', 'windows_event', 'firewall_log', 'agent_telemetry').")
    host_identifier: Optional[str] = Field(None, example="server-prod-01", description="Identifier for the host originating the log.")
    timestamp: Optional[datetime.datetime] = Field(None, description="Timestamp of the event from the log itself. If not provided, server time will be used.")
    initial_metadata: Optional[Dict[str, Any]] = Field(None, description="Any initial metadata from the ingestion agent.")

class RawLogEventCreate(RawLogEventBase):
    pass

class RawLogEventResponse(RawLogEventBase):
    id: int
    ingested_at: datetime.datetime

    class Config:
        orm_mode = True

@router.post("/ingest/", response_model=RawLogEventResponse, status_code=status.HTTP_201_CREATED)
def ingest_single_log_event(log_event: RawLogEventCreate, db: Session = Depends(get_db)):
    """
    Ingest a single raw log event into the SIEM.
    """
    db_log = crud.create_raw_log_event(
        db=db,
        raw_log_data=log_event.raw_log_data,
        source_type=log_event.source_type,
        host_identifier=log_event.host_identifier,
        timestamp=log_event.timestamp,
        initial_metadata=log_event.initial_metadata
    )
    return db_log

@router.post("/ingest/batch", response_model=List[RawLogEventResponse], status_code=status.HTTP_201_CREATED)
def ingest_batch_log_events(log_events: List[RawLogEventCreate], db: Session = Depends(get_db)):
    """
    Ingest multiple raw log events into the SIEM in a single batch.
    """
    created_logs = []
    for log_event in log_events:
        db_log = crud.create_raw_log_event(
            db=db,
            raw_log_data=log_event.raw_log_data,
            source_type=log_event.source_type,
            host_identifier=log_event.host_identifier,
            timestamp=log_event.timestamp,
            initial_metadata=log_event.initial_metadata
        )
        created_logs.append(db_log)
    return created_logs

@router.get("/logs/{log_id}", response_model=RawLogEventResponse)
def get_log_event_by_id(log_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific raw log event by its ID.
    """
    db_log = crud.get_raw_log_event(db, log_id=log_id)
    if db_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log event not found")
    return db_log

@router.get("/logs/", response_model=List[RawLogEventResponse])
def get_log_events(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[str] = None,
    host_identifier: Optional[str] = None,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve raw log events with optional filters.
    """
    logs = crud.get_raw_log_events(
        db=db,
        skip=skip,
        limit=limit,
        source_type=source_type,
        host_identifier=host_identifier,
        start_time=start_time,
        end_time=end_time
    )
    return logs
