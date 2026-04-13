# backend_api/attack_graph_engine/graph_model.py
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

# --- Node Types ---

class BaseNode(BaseModel):
    node_id: str = Field(description="Unique identifier for the node")
    node_type: str = Field(description="The type of the node")
    last_seen: float = Field(description="Timestamp of the last update")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Flexible key-value attributes")

class HostNode(BaseNode):
    node_type: Literal["Host"] = "Host"
    hostname: Optional[str] = None
    os: Optional[str] = None

class ProcessNode(BaseNode):
    node_type: Literal["Process"] = "Process"
    process_name: str
    pid: int
    command_line: Optional[str] = None

class IPAddressNode(BaseNode):
    node_type: Literal["IPAddress"] = "IPAddress"
    ip_address: str

class VulnerabilityNode(BaseNode):
    node_type: Literal["Vulnerability"] = "Vulnerability"
    cve_id: str
    severity: str # e.g., "Critical", "High"
    cvss_score: float

class UserNode(BaseNode):
    node_type: Literal["User"] = "User"
    username: str

# --- Edge Types ---

class BaseEdge(BaseModel):
    source: str = Field(description="Node ID of the source node")
    target: str = Field(description="Node ID of the target node")
    edge_type: str = Field(description="The type of the relationship")
    last_seen: float = Field(description="Timestamp of the last update")
    weight: float = Field(default=1.0, description="Cost or risk associated with traversing this edge")

class ConnectedToEdge(BaseEdge):
    edge_type: Literal["CONNECTED_TO"] = "CONNECTED_TO"
    port: int
    protocol: str

class ExecutedEdge(BaseEdge):
    edge_type: Literal["EXECUTED"] = "EXECUTED"

class HasVulnerabilityEdge(BaseEdge):
    edge_type: Literal["HAS_VULNERABILITY"] = "HAS_VULNERABILITY"

class LoggedIntoEdge(BaseEdge):
    edge_type: Literal["LOGGED_INTO"] = "LOGGED_INTO"
