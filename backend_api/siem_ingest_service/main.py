from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from . import crud, models
from .database import engine, get_db
from loguru import logger
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, FastAPI
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

router = APIRouter()

class RawLogEventBase(BaseModel):
    raw_log_data: str = Field(..., example="<13>Jan 1 00:00:00 hostname program: Message content")
    source_type: str = Field(..., example="syslog")
    host_identifier: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None
    initial_metadata: Optional[Dict[str, Any]] = None

class RawLogEventCreate(RawLogEventBase):
    pass

class RawLogEventResponse(RawLogEventBase):
    id: int
    ingested_at: datetime.datetime

    class Config:
        from_attributes = True

@router.post("/ingest/", response_model=RawLogEventResponse, status_code=status.HTTP_201_CREATED)
def ingest_single_log_event(log_event: RawLogEventCreate, db: Session = Depends(get_db)):
    """
    Ingest a single raw log event into the SIEM.
    """
    try:
        db_log = crud.create_raw_log_event(
            db=db,
            raw_log_data=log_event.raw_log_data,
            source_type=log_event.source_type,
            host_identifier=log_event.host_identifier,
            timestamp=log_event.timestamp,
            initial_metadata=log_event.initial_metadata
        )
        return success_response(data=db_log)
    except Exception as e:
        logger.error(f"Failed to ingest log: {e}")
        return error_response(code="INGEST_FAILED", message=str(e), status_code=500)

@router.post("/ingest/batch", response_model=List[RawLogEventResponse], status_code=status.HTTP_201_CREATED)
def ingest_batch_log_events(log_events: List[RawLogEventCreate], db: Session = Depends(get_db)):
    """
    Ingest multiple raw log events in a single batch.
    """
    try:
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
        return success_response(data=created_logs)
    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        return error_response(code="BATCH_INGEST_FAILED", message=str(e), status_code=500)

@router.get("/logs/{log_id}", response_model=RawLogEventResponse)
def get_log_event_by_id(log_id: int, db: Session = Depends(get_db)):
    db_log = crud.get_raw_log_event(db, log_id=log_id)
    if db_log is None:
        return error_response(code="NOT_FOUND", message="Log event not found", status_code=404)
    return success_response(data=db_log)

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
    logs = crud.get_raw_log_events(
        db=db, skip=skip, limit=limit, source_type=source_type,
        host_identifier=host_identifier, start_time=start_time, end_time=end_time
    )
    return success_response(data=logs)

async def siem_ingest_startup(app: FastAPI):
    """
    Handles startup events for the SIEM Ingest Service.
    """
    models.Base.metadata.create_all(bind=engine)
    logger.info("SIEM Ingest Service: Database tables initialized.")

app = create_phantom_service(
    name="SIEM Ingest Service",
    description="High-throughput raw log ingestion engine for SIEM integration.",
    version="1.0.0",
    custom_startup=siem_ingest_startup
)

app.include_router(router, prefix="/api/v1/siem")
