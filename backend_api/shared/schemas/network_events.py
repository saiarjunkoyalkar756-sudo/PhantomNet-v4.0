from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class PacketMetadata(BaseModel):
    """Schema for basic packet metadata."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the packet was observed (UTC).")
    src_ip: str = Field(..., description="Source IP address.")
    dst_ip: str = Field(..., description="Destination IP address.")
    src_port: Optional[int] = Field(None, description="Source port, if applicable.")
    dst_port: Optional[int] = Field(None, description="Destination port, if applicable.")
    protocol: str = Field(..., description="Network protocol (e.g., TCP, UDP, ICMP, HTTP, DNS).")
    length: int = Field(..., description="Length of the packet in bytes.")
    flags: Optional[str] = Field(None, description="TCP flags (e.g., SYN, ACK, FIN), if applicable.")

class DpiMetadata(BaseModel):
    """Schema for Deep Packet Inspection (DPI) inferred metadata."""
    app_protocol: Optional[str] = Field(None, description="Inferred application-layer protocol (e.g., HTTP, TLS, SSH, FTP).")
    tls_sni: Optional[str] = Field(None, description="TLS Server Name Indication (SNI), if observed.")
    http_method: Optional[str] = Field(None, description="HTTP method (e.g., GET, POST), if observed.")
    http_host: Optional[str] = Field(None, description="HTTP Host header, if observed.")
    dns_query: Optional[str] = Field(None, description="DNS query, if observed.")
    content_category: Optional[str] = Field(None, description="Categorization of content (e.g., social media, news, malware), if inferred.")

class ConnectionGraphNode(BaseModel):
    """Represents a node in the network connection graph."""
    ip_address: str = Field(..., description="IP address of the node.")
    hostname: Optional[str] = Field(None, description="Resolved hostname, if available.")
    roles: Optional[list[str]] = Field(None, description="Roles of the node (e.g., 'server', 'client', 'workstation').")

class ConnectionGraphEdge(BaseModel):
    """Represents an edge (connection) in the network connection graph."""
    source_ip: str = Field(..., description="Source IP address of the connection.")
    destination_ip: str = Field(..., description="Destination IP address of the connection.")
    protocol: str = Field(..., description="Protocol used for the connection.")
    port: Optional[int] = Field(None, description="Port used for the connection.")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the connection started.")
    end_time: Optional[datetime] = Field(None, description="Timestamp when the connection ended, if known.")
    byte_count: Optional[int] = Field(None, description="Total bytes transferred over the connection.")
    packet_count: Optional[int] = Field(None, description="Total packets transferred over the connection.")

class FlowMlFeatures(BaseModel):
    """Schema for flow-based machine learning features (NetFlow-like)."""
    flow_id: str = Field(..., description="Unique identifier for the flow.")
    duration_ms: int = Field(..., description="Duration of the flow in milliseconds.")
    total_fwd_packets: int = Field(..., description="Total packets in the forward direction.")
    total_bwd_packets: int = Field(..., description="Total packets in the backward direction.")
    total_fwd_bytes: int = Field(..., description="Total bytes in the forward direction.")
    total_bwd_bytes: int = Field(..., description="Total bytes in the backward direction.")
    fwd_IAT_mean: float = Field(..., description="Mean inter-arrival time for forward packets.")
    bwd_IAT_mean: float = Field(..., description="Mean inter-arrival time for backward packets.")
    fwd_packet_length_max: int = Field(..., description="Maximum packet length in forward direction.")
    bwd_packet_length_mean: float = Field(..., description="Mean packet length in backward direction.")
    # Add more NetFlow-like features as needed

class DetectionInfo(BaseModel):
    """Schema for detection information related to suspicious activities."""
    detection_type: str = Field(..., description="Type of detection (e.g., 'suspicious_connection', 'dns_anomaly', 'c2_pattern').")
    severity: str = Field(..., description="Severity of the detection (e.g., 'low', 'medium', 'high', 'critical').")
    description: str = Field(..., description="Detailed description of the detected activity.")
    matched_patterns: Optional[list[str]] = Field(None, description="List of patterns that triggered the detection.")
    confidence: float = Field(..., description="Confidence score of the detection (0.0 to 1.0).")
    recommended_action: Optional[str] = Field(None, description="Suggested action for the detected activity.")

class NetworkEvent(BaseModel):
    """Unified schema for various network telemetry events."""
    agent_id: str = Field(..., description="Unique identifier of the PhantomNet agent.")
    event_type: str = Field(..., description="Type of network event (e.g., 'packet_metadata', 'dpi_metadata', 'connection_flow', 'detection').")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the event (UTC).")
    
    # Common network flow fields (could be redundant with PacketMetadata/FlowMlFeatures but good for top-level context)
    src_ip: Optional[str] = Field(None, description="Source IP address of the event.")
    dst_ip: Optional[str] = Field(None, description="Destination IP address of the event.")
    src_port: Optional[int] = Field(None, description="Source port of the event.")
    dst_port: Optional[int] = Field(None, description="Destination port of the event.")
    protocol: Optional[str] = Field(None, description="Protocol related to the event.")

    # Specific event payloads
    packet_metadata: Optional[PacketMetadata] = Field(None, description="Detailed packet metadata.")
    dpi_metadata: Optional[DpiMetadata] = Field(None, description="Deep Packet Inspection inferred metadata.")
    connection_graph_nodes: Optional[list[ConnectionGraphNode]] = Field(None, description="Nodes for network connection graph updates.")
    connection_graph_edges: Optional[list[ConnectionGraphEdge]] = Field(None, description="Edges for network connection graph updates.")
    flow_ml_features: Optional[FlowMlFeatures] = Field(None, description="Flow-based machine learning features.")
    detection_info: Optional[DetectionInfo] = Field(None, description="Information about detected suspicious activity.")

    # Raw data or additional context if needed
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw data associated with the event, if applicable.")

