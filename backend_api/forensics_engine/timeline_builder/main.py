from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import uuid

router = APIRouter()

class TimelineEvent(BaseModel):
    timestamp: datetime.datetime = Field(..., description="Timestamp of the event.")
    event_type: str = Field(..., example="process_creation", description="Type of forensic event (e.g., 'file_modification', 'network_connection').")
    description: str = Field(..., description="Description of the event.")
    source: str = Field(..., example="syslog", description="Source of the event data (e.g., 'syslog', 'memory_dump', 'disk_image').")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed forensic information about the event.")

class TimelineRequest(BaseModel):
    asset_id: str = Field(..., example="compromised-server-01")
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    data_sources: List[str] = Field(default_factory=list, example=["logs", "memory", "disk_image"])

class TimelineResponse(BaseModel):
    job_id: str = Field(..., description="ID of the associated forensic job.")
    asset_id: str = Field(..., example="compromised-server-01")
    timeline_events: List[TimelineEvent] = Field(default_factory=list)
    status: str = Field(..., example="completed")

@router.post("/build/", response_model=TimelineResponse)
async def build_forensic_timeline(request: TimelineRequest):
    """
    Simulates building a forensic timeline for a given asset based on specified data sources.
    """
    timeline_events = []
    
    # Simulate data collection and timeline reconstruction
    # In a real scenario, this would query various data sources (logs, EDR, agent data)
    # and organize them chronologically.
    
    # Example 1: Simulate process creation events from logs
    if "logs" in request.data_sources:
        timeline_events.append(TimelineEvent(
            timestamp=datetime.datetime.now() - datetime.timedelta(hours=2),
            event_type="process_creation",
            description=f"Process 'malware.exe' started on {request.asset_id}",
            source="system_logs",
            details={"process_name": "malware.exe", "user": "admin", "pid": 1234}
        ))
        timeline_events.append(TimelineEvent(
            timestamp=datetime.datetime.now() - datetime.timedelta(hours=1, minutes=30),
            event_type="network_connection",
            description=f"Outbound connection from {request.asset_id} to C2 server 1.2.3.4",
            source="network_logs",
            details={"destination_ip": "1.2.3.4", "destination_port": 443, "protocol": "TCP"}
        ))
    
    # Example 2: Simulate file modification events from a disk image analysis
    if "disk_image" in request.data_sources:
        timeline_events.append(TimelineEvent(
            timestamp=datetime.datetime.now() - datetime.timedelta(hours=3),
            event_type="file_modification",
            description=f"File '/etc/passwd' modified on {request.asset_id}",
            source="disk_analysis",
            details={"file_path": "/etc/passwd", "user": "root"}
        ))
    
    # Sort events by timestamp
    timeline_events.sort(key=lambda x: x.timestamp)

    return TimelineResponse(
        job_id=str(uuid.uuid4()), # Placeholder job ID
        asset_id=request.asset_id,
        timeline_events=timeline_events,
        status="completed"
    )
