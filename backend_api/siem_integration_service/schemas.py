from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class RawLog(BaseModel):
    """Represents a raw log event before normalization."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_system: str
    host: Optional[str] = None
    raw_data: str

class NormalizedLog(BaseModel):
    """Represents a normalized log event based on a common schema."""
    event_id: str = Field(..., description="Unique ID for the normalized event.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(..., description="Categorized type of the event (e.g., 'auth.login', 'process.create', 'network.connection').")
    severity: Optional[str] = None # e.g., 'info', 'warning', 'error', 'critical'
    source_system: str
    host_id: Optional[str] = None # ID of the host where the event occurred
    host_ip: Optional[str] = None
    user: Optional[str] = None
    process_name: Optional[str] = None
    process_id: Optional[int] = None
    file_path: Optional[str] = None
    network_protocol: Optional[str] = None
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    message: str = Field(..., description="A concise, human-readable summary of the event.")
    full_data: Dict[str, Any] = Field(default_factory=dict, description="Full normalized event data.")
    raw_log_id: Optional[str] = None # Link back to the raw log

class PhantomQLQuery(BaseModel):
    """Represents a PhantomQL query."""
    query_string: str = Field(..., description="The PhantomQL query string.")
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = 0

class QueryResult(BaseModel):
    """Represents the result of a PhantomQL query."""
    total_hits: int
    took_ms: int
    logs: List[NormalizedLog]

class DashboardWidgetConfig(BaseModel):
    """Configuration for a dashboard widget."""
    widget_id: str
    widget_type: str # e.g., "chart", "table", "metric"
    title: str
    query: PhantomQLQuery
    visualization_options: Dict[str, Any]

# Multi-tenant specific models (conceptual - requires tenant management)
class Workspace(BaseModel):
    """Represents a multi-tenant workspace."""
    workspace_id: str
    name: str
    description: Optional[str] = None
    owner_user_id: str
    # Access control list, etc.
