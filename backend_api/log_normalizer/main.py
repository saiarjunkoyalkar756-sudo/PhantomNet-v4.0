from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .event_schema import NormalizedLogEvent
from loguru import logger
import datetime
import uuid
import re
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, FastAPI, Request
from pydantic import BaseModel, Field

router = APIRouter()

class RawLogData(BaseModel):
    raw_log: str = Field(..., example="<13>Jan 1 00:00:00 hostname program: Message content")
    source_type: str = Field(..., example="syslog")
    host_identifier: Optional[str] = None

def _normalize_syslog(raw_log: str, source_type: str, host_identifier: Optional[str]) -> NormalizedLogEvent:
    match = re.match(r"<(\d+)>(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+([\w\d\.-]+)\s+([^:]+):\s+(.*)", raw_log)
    if match:
        priority_val, date_str, host, program, message = match.groups()
        severity_map = {0: "Emergency", 1: "Alert", 2: "Critical", 3: "Error", 4: "Warning", 5: "Notice", 6: "Informational", 7: "Debug"}
        severity = severity_map.get(int(priority_val) % 8, "Informational")
        try:
            current_year = datetime.datetime.now().year
            timestamp_str = f"{date_str} {current_year}"
            timestamp = datetime.datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
        except ValueError:
            timestamp = datetime.datetime.now()

        return NormalizedLogEvent(
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            event_type="system_event",
            severity=severity,
            message=message,
            source_type=source_type,
            source_host=host_identifier if host_identifier else host,
            original_raw_log=raw_log,
            metadata={"program": program, "syslog_priority": int(priority_val)}
        )
    raise ValueError("Syslog format not recognized")

def _normalize_windows_event(raw_log: str, source_type: str, host_identifier: Optional[str]) -> NormalizedLogEvent:
    event_id_match = re.search(r"Event ID (\d+):", raw_log)
    message_match = re.search(r":\s+(.*)", raw_log)
    user_match = re.search(r"User=(.+)", raw_log)
    
    event_id = event_id_match.group(1) if event_id_match else "unknown"
    message = message_match.group(1).strip() if message_match else raw_log
    user = user_match.group(1) if user_match else None

    return NormalizedLogEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(),
        event_type="auth" if "logged on" in message.lower() else "system_event",
        severity="Informational",
        message=message,
        source_type=source_type,
        source_host=host_identifier,
        user=user,
        original_raw_log=raw_log,
        metadata={"windows_event_id": event_id}
    )

@router.post("/normalize/", response_model=NormalizedLogEvent)
async def normalize_log_event(log_data: RawLogData):
    """
    Receives raw log data and normalizes it into a structured event.
    """
    try:
        if log_data.source_type == "syslog":
            result = _normalize_syslog(log_data.raw_log, log_data.source_type, log_data.host_identifier)
        elif log_data.source_type == "windows_event":
            result = _normalize_windows_event(log_data.raw_log, log_data.source_type, log_data.host_identifier)
        else:
            result = NormalizedLogEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.datetime.now(),
                event_type="unhandled_event",
                severity="Informational",
                message=log_data.raw_log,
                source_type=log_data.source_type,
                source_host=log_data.host_identifier,
                original_raw_log=log_data.raw_log,
                metadata={"parser_status": "unsupported_source_type"}
            )
        return success_response(data=result.model_dump())
    except ValueError as e:
        logger.warning(f"Normalization failed: {e}")
        return error_response(code="NORMALIZATION_FAILED", message=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return error_response(code="INTERNAL_ERROR", message=str(e), status_code=500)

@router.post("/normalize/batch", response_model=List[NormalizedLogEvent])
async def normalize_log_events_batch(log_data_list: List[RawLogData]):
    """
    Receives a list of raw log data and normalizes them into structured events in batch.
    """
    normalized_events = []
    for log_data in log_data_list:
        try:
            # We call the logic directly to avoid multiple envelope wraps if calling the endpoint function
            if log_data.source_type == "syslog":
                res = _normalize_syslog(log_data.raw_log, log_data.source_type, log_data.host_identifier)
            elif log_data.source_type == "windows_event":
                res = _normalize_windows_event(log_data.raw_log, log_data.source_type, log_data.host_identifier)
            else:
                res = NormalizedLogEvent(
                    event_id=str(uuid.uuid4()),
                    timestamp=datetime.datetime.now(),
                    event_type="unhandled_event",
                    severity="Informational",
                    message=log_data.raw_log,
                    source_type=log_data.source_type,
                    source_host=log_data.host_identifier,
                    original_raw_log=log_data.raw_log,
                    metadata={"parser_status": "unsupported_source_type"}
                )
            normalized_events.append(res.model_dump())
        except Exception:
            continue
    return success_response(data=normalized_events)

app = create_phantom_service(
    name="Log Normalizer Service",
    description="Transforms raw log strings from various sources into a standardized, machine-readable schema for downstream analysis.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1/normalizer")
