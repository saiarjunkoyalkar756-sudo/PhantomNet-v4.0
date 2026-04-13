from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from loguru import logger
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from iam_service.auth_methods import get_current_user, User, UserRole, has_role
from shared.database import get_db, AttackLog
from backend_api.siem_ingest_service import crud as siem_crud
from backend_api.siem_ingest_service.database import get_db as get_siem_db
from backend_api.siem_ingest_service.models import RawLogEvent

router = APIRouter()

class RawLogResponse(BaseModel):
    id: int
    timestamp: datetime
    source_type: str
    host_identifier: Optional[str]
    raw_log_data: str
    ingested_at: datetime
    initial_metadata: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True

@router.get(
    "/logs",
    dependencies=[
        Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))
    ],
)
def get_logs(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    print(f"get_logs db: {db}")
    logs = db.query(AttackLog).order_by(AttackLog.timestamp.desc()).all()
    # Convert AttackLog objects to dictionaries or a suitable format for the frontend
    logger.info(f"User ID: {current_user.id} fetched logs.")  # Redact username
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "ip": log.ip,
                "port": log.port,
                "data": log.data,
                "attack_type": log.attack_type,
                "confidence_score": log.confidence_score,
                "is_anomaly": log.is_anomaly,
                "anomaly_score": log.anomaly_score,
                "is_verified_threat": log.is_verified_threat,
                "is_blacklisted": log.is_blacklisted,
            }
            for log in logs
        ]
    }

@router.get(
    "/logs/poll",
    response_model=List[RawLogResponse],
    dependencies=[
        Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))
    ],
)
def poll_logs(
    limit: int = 100,
    since: Optional[datetime] = None,
    db: Session = Depends(get_siem_db)
):
    """
    Poll for recent raw log events.
    """
    logs = siem_crud.get_raw_log_events(db, limit=limit, start_time=since)
    return logs
