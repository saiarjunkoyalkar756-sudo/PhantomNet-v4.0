from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import datetime

class NormalizedLogEvent(BaseModel):
    # Core event fields
    event_id: str = Field(..., description="Unique identifier for the normalized event.")
    timestamp: datetime.datetime = Field(..., description="Timestamp of the event.")
    event_type: str = Field(..., description="High-level type of the event (e.g., 'auth', 'network', 'process', 'file_access').")
    severity: str = Field(..., description="Severity of the event (e.g., 'Informational', 'Low', 'Medium', 'High', 'Critical').")
    message: str = Field(..., description="Human-readable message summarizing the event.")
    
    # Source information
    source_type: str = Field(..., description="Original source type of the log (e.g., 'syslog', 'windows_event', 'agent_telemetry').")
    source_host: Optional[str] = Field(None, description="Hostname or IP of the system where the event occurred.")
    source_ip: Optional[str] = Field(None, description="Source IP address related to the event.")
    source_port: Optional[int] = Field(None, description="Source port related to the event.")
    
    # Destination information (for network events)
    destination_host: Optional[str] = Field(None, description="Destination hostname or IP for network events.")
    destination_ip: Optional[str] = Field(None, description="Destination IP address for network events.")
    destination_port: Optional[int] = Field(None, description="Destination port for network events.")
    
    # User/Process information
    user: Optional[str] = Field(None, description="User associated with the event.")
    process_name: Optional[str] = Field(None, description="Process name associated with the event.")
    process_id: Optional[int] = Field(None, description="Process ID associated with the event.")
    
    # File information (for file access events)
    file_path: Optional[str] = Field(None, description="File path involved in the event.")
    file_hash: Optional[str] = Field(None, description="Hash of the file involved in the event.")
    
    # Network information
    protocol: Optional[str] = Field(None, example="TCP", description="Network protocol.")
    action: Optional[str] = Field(None, example="ALLOW", description="Action taken (e.g., ALLOW, DENY, CREATE, DELETE).")

    # Raw log data for reference
    original_raw_log: str = Field(..., description="The original raw log string.")
    
    # Additional context/metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured metadata about the event.")

    # Time of normalization
    normalized_at: datetime.datetime = Field(default_factory=datetime.datetime.now, description="Timestamp when the event was normalized.")
