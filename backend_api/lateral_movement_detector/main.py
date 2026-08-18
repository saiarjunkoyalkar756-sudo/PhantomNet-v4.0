# backend_api/lateral_movement_detector/main.py
from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from ..log_normalizer.event_schema import NormalizedLogEvent
from loguru import logger
import uuid
import datetime
import ipaddress
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, FastAPI, Request
from pydantic import BaseModel, Field

router = APIRouter()

class LateralMovementDetection(BaseModel):
    detection_id: str = Field(..., json_schema_extra={"example": "LM-2023-001"})
    timestamp: datetime.datetime
    event_type: str
    technique_id: Optional[str] = None
    technique_name: Optional[str] = None
    description: str
    severity: str
    source_event_ids: List[str] = Field(default_factory=list)
    involved_assets: List[str] = Field(default_factory=list)
    involved_users: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)

class LateralMovementDetectionRequest(BaseModel):
    events: List[NormalizedLogEvent]

class LateralMovementDetectionResponse(BaseModel):
    detections: List[LateralMovementDetection]

def is_ip_internal(ip_str: str) -> bool:
    """Helper to check if an IP is within a private internal subnet using ipaddress."""
    try:
        ip = ipaddress.ip_address(ip_str)
        internal_nets = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("127.0.0.0/8")
        ]
        return any(ip in net for net in internal_nets)
    except ValueError:
        return False

@router.post("/detect/", response_model=LateralMovementDetectionResponse)
async def detect_lateral_movement_endpoint(request: LateralMovementDetectionRequest):
    """
    Analyzes a batch of normalized log events to detect potential lateral movement attempts.
    """
    detections = []
    
    for event in request.events:
        # Example 1: Unusual RDP/SSH login to a critical server
        if event.event_type == "auth" and event.action == "login_success":
            dest_host = getattr(event, "destination_host", "") or ""
            is_critical_host = any(k in dest_host.lower() for k in ["prod", "critical", "db", "vault", "dc"])
            
            if event.destination_port in [22, 3389] and is_critical_host:
                if not is_ip_internal(event.source_ip):
                    detections.append(
                        LateralMovementDetection(
                            detection_id=f"LM-{uuid.uuid4().hex[:8]}",
                            timestamp=datetime.datetime.now(datetime.timezone.utc),
                            event_type="lateral_movement_detected",
                            technique_id="T1021",
                            technique_name="Remote Services: SSH/RDP",
                            description=f"Unusual {event.protocol} login from external IP {event.source_ip} to critical server {dest_host}.",
                            severity="Critical",
                            source_event_ids=[event.event_id],
                            involved_assets=[event.source_host, dest_host] if hasattr(event, "source_host") else [dest_host],
                            involved_users=[event.user] if event.user else [],
                            additional_data={"source_ip": event.source_ip, "destination_port": event.destination_port}
                        )
                    )
        
        # Example 2: Process creation on a remote host via PSExec-like activity
        if event.event_type == "process" and event.process_name == "psexec.exe":
            remote_target = event.metadata.get("remote_target") if event.metadata else None
            if remote_target:
                source_host = getattr(event, "source_host", "unknown")
                detections.append(
                    LateralMovementDetection(
                        detection_id=f"LM-{uuid.uuid4().hex[:8]}",
                        timestamp=datetime.datetime.now(datetime.timezone.utc),
                        event_type="lateral_movement_detected",
                        technique_id="T1569.002",
                        technique_name="System Services: Service Execution",
                        description=f"Potential PSExec-like activity detected from {source_host} to {remote_target}.",
                        severity="High",
                        source_event_ids=[event.event_id],
                        involved_assets=[source_host, remote_target],
                        involved_users=[event.user] if event.user else [],
                        additional_data={"process_command_line": event.message}
                    )
                )

    return LateralMovementDetectionResponse(detections=detections)

app = create_phantom_service(
    name="Lateral Movement Detector",
    description="Analyzes security events to identify patterns of host-to-host movement.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1/lateral-movement", tags=["detection"])