from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .database import get_db, initialize_database
from . import crud
import datetime
from loguru import logger

router = APIRouter()


async def audit_log_collector_startup(app: FastAPI) -> None:
    """Initialize the collector-owned audit schema before accepting persisted audit records."""
    initialize_database()


app = create_phantom_service(
    name="Audit Log Collector",
    description="Centralized audit log collection and indexing service.",
    version="1.0.0",
    custom_startup=audit_log_collector_startup,
    required_dependencies=("database",),
)
app.include_router(router)

class AuditLogBase(BaseModel):
    raw_log_data: str = Field(..., json_schema_extra={"example": "User 'admin' logged in from 192.168.1.100"})
    action: str = Field(..., json_schema_extra={"example": "login"})
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
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingested_at: datetime.datetime

async def _mirror_alert_to_optional_ledger(audit_log: AuditLogCreate) -> None:
    """Mirror an already-persisted alert audit record only when the optional ledger is available."""
    if "alert" not in audit_log.action.lower():
        return
    try:
        from blockchain_layer.blockchain_client import submit_alert_to_ledger
    except ModuleNotFoundError:
        logger.info("Optional audit ledger mirror is not configured; persisted audit ingestion continues.")
        return

    metadata = audit_log.metadata or {}
    try:
        await submit_alert_to_ledger(
            alert_id=audit_log.event_id or "UNSPECIFIED-AUDIT-EVENT",
            alert_name=audit_log.raw_log_data,
            severity=metadata.get("severity", "high"),
            event_data=metadata,
        )
    except Exception:
        logger.exception("Optional audit ledger mirror failed after durable audit persistence.")


@router.post("/ingest/", status_code=status.HTTP_201_CREATED)
async def ingest_single_audit_log(audit_log: AuditLogCreate, db: Session = Depends(get_db)):
    db_audit = crud.create_audit_log(db=db, **audit_log.model_dump())
    await _mirror_alert_to_optional_ledger(audit_log)
    return success_response(data=db_audit)

@router.post("/ingest/batch", status_code=status.HTTP_201_CREATED)
async def ingest_batch_audit_logs(audit_logs: List[AuditLogCreate], db: Session = Depends(get_db)):
    created_logs = []
    for audit_log in audit_logs:
        db_audit = crud.create_audit_log(db=db, **audit_log.model_dump())
        created_logs.append(db_audit)
        await _mirror_alert_to_optional_ledger(audit_log)
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
