from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Union, Dict, Any

from ..iam_service.auth_methods import get_current_user, User, UserRole, has_role
from ..telemetry_ingest import TelemetryIngestService
from ..services import get_telemetry_ingest_service

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

class CustomLogEntry(BaseModel):
    source: str = Field(..., description="The source of the log (e.g., 'my-custom-app').")
    log_entry: Union[str, Dict[str, Any]] = Field(..., description="The log entry to ingest.")

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_custom_log(
    log: CustomLogEntry,
    current_user: User = Depends(get_current_user),
    telemetry_service: TelemetryIngestService = Depends(get_telemetry_ingest_service)
):
    """
    Ingests a custom log entry from a user-defined source.
    """
    if not telemetry_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telemetry Ingest Service not available."
        )

    await telemetry_service.ingest_raw_log(log.log_entry, log.source)
    return {"message": "Log entry accepted for ingestion."}
