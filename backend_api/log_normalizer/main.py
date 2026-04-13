from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import uuid
import re

from .event_schema import NormalizedLogEvent

router = APIRouter()

class RawLogData(BaseModel):
    raw_log: str = Field(..., example="<13>Jan 1 00:00:00 hostname program: Message content")
    source_type: str = Field(..., example="syslog", description="Original source type of the log.")
    host_identifier: Optional[str] = Field(None, example="server-prod-01")


def _normalize_syslog(raw_log: str, source_type: str, host_identifier: Optional[str]) -> NormalizedLogEvent:
    """
    Simulated normalization for a basic syslog-like format.
    Example: '<13>Jan 1 00:00:00 hostname program: Message content'
    """
    match = re.match(r"<(\d+)>(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+([\w\d\.-]+)\s+([^:]+):\s+(.*)", raw_log)
    if match:
        priority_val, date_str, host, program, message = match.groups()
        
        # Simple mapping for severity from syslog priority (very basic)
        # This would be more complex in a real system
        severity_map = {0: "Emergency", 1: "Alert", 2: "Critical", 3: "Error", 4: "Warning", 5: "Notice", 6: "Informational", 7: "Debug"}
        severity = severity_map.get(int(priority_val) % 8, "Informational")

        # Attempt to parse timestamp (this is highly simplified and might need year inference)
        try:
            # Assuming current year for simplicity; real parsers handle year properly
            current_year = datetime.datetime.now().year
            timestamp_str = f"{date_str} {current_year}"
            timestamp = datetime.datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
        except ValueError:
            timestamp = datetime.datetime.now() # Fallback

        return NormalizedLogEvent(
            event_id=str(uuid.uuid4()),
            timestamp=timestamp,
            event_type="system_event", # General type
            severity=severity,
            message=message,
            source_type=source_type,
            source_host=host_identifier if host_identifier else host,
            original_raw_log=raw_log,
            metadata={"program": program, "syslog_priority": int(priority_val)}
        )
    raise ValueError("Syslog format not recognized")

def _normalize_windows_event(raw_log: str, source_type: str, host_identifier: Optional[str]) -> NormalizedLogEvent:
    """
    Simulated normalization for a basic Windows Event Log-like format (as a string).
    Example: 'Event ID 4624: An account was successfully logged on. Subject: User=Admin'
    """
    event_id_match = re.search(r"Event ID (\d+):", raw_log)
    message_match = re.search(r":\s+(.*)", raw_log)
    user_match = re.search(r"User=(.+)", raw_log)
    
    event_id = event_id_match.group(1) if event_id_match else "unknown"
    message = message_match.group(1).strip() if message_match else raw_log
    user = user_match.group(1) if user_match else None

    event_type = "auth" if "logged on" in message.lower() or "logon" in message.lower() else "system_event"
    severity = "Informational" # Default; real parser would extract from event data

    return NormalizedLogEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(), # In real logs, timestamp would be parsed
        event_type=event_type,
        severity=severity,
        message=message,
        source_type=source_type,
        source_host=host_identifier,
        user=user,
        original_raw_log=raw_log,
        metadata={"windows_event_id": event_id}
    )
    # raise ValueError("Windows event format not recognized") # For more strict parsing

@router.post("/normalize/", response_model=NormalizedLogEvent)
async def normalize_log_event(log_data: RawLogData):
    """
    Receives raw log data and normalizes it into a structured event.
    """
    if log_data.source_type == "syslog":
        try:
            return _normalize_syslog(log_data.raw_log, log_data.source_type, log_data.host_identifier)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Syslog normalization failed: {e}")
    elif log_data.source_type == "windows_event":
        try:
            return _normalize_windows_event(log_data.raw_log, log_data.source_type, log_data.host_identifier)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Windows event normalization failed: {e}")
    else:
        # Fallback for unhandled source types
        return NormalizedLogEvent(
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

@router.post("/normalize/batch", response_model=List[NormalizedLogEvent])
async def normalize_log_events_batch(log_data_list: List[RawLogData]):
    """
    Receives a list of raw log data and normalizes them into structured events in batch.
    """
    normalized_events = []
    for log_data in log_data_list:
        try:
            normalized_event = await normalize_log_event(log_data)
            normalized_events.append(normalized_event)
        except HTTPException as e:
            # For batch, we might want to log errors and continue, or return partial success.
            # For simplicity, if one fails, we just don't add it to the list.
            print(f"Failed to normalize one log in batch: {e.detail}")
        except Exception as e:
            print(f"Unexpected error during batch normalization: {e}")
    return normalized_events

