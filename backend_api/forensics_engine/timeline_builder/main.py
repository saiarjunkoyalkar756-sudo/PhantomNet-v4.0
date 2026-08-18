# backend_api/forensics_engine/timeline_builder/main.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import uuid

router = APIRouter()

class TimelineEvent(BaseModel):
    timestamp: datetime.datetime = Field(..., description="Timestamp of the event.")
    event_type: str = Field(..., json_schema_extra={"example": "process_creation"}, description="Type of forensic event (e.g., 'file_modification', 'network_connection').")
    description: str = Field(..., description="Description of the event.")
    source: str = Field(..., json_schema_extra={"example": "syslog"}, description="Source of the event data (e.g., 'syslog', 'memory_dump', 'disk_image').")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed forensic information about the event.")

class TimelineRequest(BaseModel):
    asset_id: str = Field(..., json_schema_extra={"example": "compromised-server-01"})
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    data_sources: List[str] = Field(default_factory=list, json_schema_extra={"example": ["logs", "memory", "disk_image"]})

class TimelineResponse(BaseModel):
    job_id: str = Field(..., description="ID of the associated forensic job.")
    asset_id: str = Field(..., json_schema_extra={"example": "compromised-server-01"})
    timeline_events: List[TimelineEvent] = Field(default_factory=list)
    status: str = Field(..., json_schema_extra={"example": "completed"})

@router.post("/build/", response_model=TimelineResponse)
async def build_forensic_timeline(request: TimelineRequest):
    """
    Builds a forensic timeline for a given asset based on specified data sources and time filters.
    """
    raw_events = []
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Simulate process creation events from logs
    if "logs" in request.data_sources:
        raw_events.append(TimelineEvent(
            timestamp=now - datetime.timedelta(hours=2),
            event_type="process_creation",
            description=f"Process 'malware.exe' started on {request.asset_id}",
            source="system_logs",
            details={"process_name": "malware.exe", "user": "admin", "pid": 1234}
        ))
        raw_events.append(TimelineEvent(
            timestamp=now - datetime.timedelta(hours=1, minutes=30),
            event_type="network_connection",
            description=f"Outbound connection from {request.asset_id} to C2 server 1.2.3.4",
            source="network_logs",
            details={"destination_ip": "1.2.3.4", "destination_port": 443, "protocol": "TCP"}
        ))
    
    # 2. Simulate file modification events from a disk image analysis
    if "disk_image" in request.data_sources:
        raw_events.append(TimelineEvent(
            timestamp=now - datetime.timedelta(hours=3),
            event_type="file_modification",
            description=f"File '/etc/passwd' modified on {request.asset_id}",
            source="disk_analysis",
            details={"file_path": "/etc/passwd", "user": "root"}
        ))
    
    # 3. Apply time range filtering
    filtered_events = []
    for event in raw_events:
        # Normalize event timestamp to make sure it's timezone-aware if request times are timezone-aware
        e_time = event.timestamp
        if request.start_time:
            req_start = request.start_time
            if req_start.tzinfo is None:
                req_start = req_start.replace(tzinfo=datetime.timezone.utc)
            if e_time < req_start:
                continue
        if request.end_time:
            req_end = request.end_time
            if req_end.tzinfo is None:
                req_end = req_end.replace(tzinfo=datetime.timezone.utc)
            if e_time > req_end:
                continue
        filtered_events.append(event)
    
    # 4. Sort chronologically
    filtered_events.sort(key=lambda x: x.timestamp)

    return TimelineResponse(
        job_id=str(uuid.uuid4()),
        asset_id=request.asset_id,
        timeline_events=filtered_events,
        status="completed"
    )
