from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import datetime # Import datetime

# Assuming import from SIEM's NormalizedLogEvent schema
from ..log_normalizer.event_schema import NormalizedLogEvent

router = APIRouter()

class LateralMovementDetection(BaseModel):
    detection_id: str = Field(..., example="LM-2023-001")
    timestamp: datetime.datetime = Field(..., description="Time of detection.")
    event_type: str = Field(..., example="lateral_movement_detected")
    technique_id: Optional[str] = Field(None, example="T1021", description="MITRE ATT&CK Technique ID.")
    technique_name: Optional[str] = Field(None, example="Remote Services", description="MITRE ATT&CK Technique Name.")
    description: str = Field(..., example="Detected SSH login from unusual source to critical server.")
    severity: str = Field(..., example="High", description="Severity of the detected lateral movement.")
    source_event_ids: List[str] = Field(default_factory=list, description="IDs of events that triggered this detection.")
    involved_assets: List[str] = Field(default_factory=list, description="Identifiers of assets involved in the detection.")
    involved_users: List[str] = Field(default_factory=list, description="Users involved in the detection.")
    additional_data: Dict[str, Any] = Field(default_factory=dict, description="Any additional context or forensic data.")

class LateralMovementDetectionRequest(BaseModel):
    events: List[NormalizedLogEvent] = Field(..., description="List of normalized log events to analyze.")

class LateralMovementDetectionResponse(BaseModel):
    detections: List[LateralMovementDetection]


@router.post("/detect/", response_model=LateralMovementDetectionResponse)
async def detect_lateral_movement(request: LateralMovementDetectionRequest):
    """
    Analyzes a batch of normalized log events to detect potential lateral movement attempts.
    """
    detections = []
    
    # Simulated lateral movement detection logic
    # In a real system, this would involve complex correlation, state tracking, and ML models.
    for event in request.events:
        # Example 1: Unusual RDP/SSH login to a critical server
        if event.event_type == "auth" and event.action == "login_success":
            if event.destination_port in [22, 3389] and event.destination_host == "critical_server_prod":
                # Simulate a check for "unusual source"
                if event.source_ip not in ["10.0.0.0/8", "192.168.1.0/24"]: # Example of known internal ranges
                    detections.append(
                        LateralMovementDetection(
                            detection_id=f"LM-{uuid.uuid4().hex[:8]}",
                            timestamp=datetime.datetime.now(),
                            event_type="lateral_movement_detected",
                            technique_id="T1021", # Remote Services
                            technique_name="Remote Services: SSH/RDP",
                            description=f"Unusual {event.protocol} login from {event.source_ip} to critical server {event.destination_host}.",
                            severity="Critical",
                            source_event_ids=[event.event_id],
                            involved_assets=[event.source_host, event.destination_host],
                            involved_users=[event.user] if event.user else [],
                            additional_data={"source_ip": event.source_ip, "destination_port": event.destination_port}
                        )
                    )
        
        # Example 2: Process creation on a remote host via PSExec-like activity
        if event.event_type == "process" and event.process_name == "psexec.exe":
            if event.metadata.get("remote_target"):
                detections.append(
                    LateralMovementDetection(
                        detection_id=f"LM-{uuid.uuid4().hex[:8]}",
                        timestamp=datetime.datetime.now(),
                        event_type="lateral_movement_detected",
                        technique_id="T1569.002", # System Services: Service Execution
                        technique_name="System Services: PSExec",
                        description=f"Potential PSExec-like activity detected from {event.source_host} to {event.metadata['remote_target']}.",
                        severity="High",
                        source_event_ids=[event.event_id],
                        involved_assets=[event.source_host, event.metadata['remote_target']],
                        involved_users=[event.user] if event.user else [],
                        additional_data={"process_command_line": event.message}
                    )
                )

        # Example 3: Multiple failed logins followed by a successful login from different source IPs (brute force, then lateral)
        # This would require stateful tracking over time, which is beyond this stateless endpoint simulation.
        # For a simple simulation: if we see a 'login_success' after some 'login_failure' on another host
        
    return LateralMovementDetectionResponse(detections=detections)