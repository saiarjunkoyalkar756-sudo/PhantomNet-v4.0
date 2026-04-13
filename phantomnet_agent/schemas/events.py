# schemas/events.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

class AgentEvent(BaseModel):
    agent_id: str
    timestamp: datetime
    event_type: str
    payload: Dict[str, Any]

class ProcessEvent(AgentEvent):
    event_type: str = "process_event"
    pid: int
    name: str
    executable: str
    cmdline: str
    username: str
    status: str
    parent_pid: Optional[int] = None

class FileEvent(AgentEvent):
    event_type: str = "file_event"
    path: str
    operation: str  # e.g., 'created', 'modified', 'deleted', 'accessed'
    file_type: str
    size: Optional[int] = None
    hash: Optional[str] = None # e.g., MD5, SHA256

class NetworkEvent(AgentEvent):
    event_type: str = "network_event"
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    protocol: str # e.g., TCP, UDP
    direction: str # e.g., 'inbound', 'outbound'
    status: str # e.g., 'established', 'listen', 'close_wait'
    process_pid: Optional[int] = None

class DnsEvent(AgentEvent):
    event_type: str = "dns_event"
    query_name: str
    query_type: str # e.g., A, AAAA, PTR
    answer: Optional[str] = None
    resolver: Optional[str] = None
    process_pid: Optional[int] = None

class LogEvent(AgentEvent):
    event_type: str = "log_event"
    log_source: str # e.g., syslog, auth.log, custom_app_log
    severity: str
    message: str
    raw_log: Optional[str] = None

# New P2P and Registration Events
class P2PDiscoveryEvent(AgentEvent):
    event_type: str = "p2p_discovery"
    peer_address: Tuple[str, int]
    sender_agent_id: str

class P2PGossipEvent(AgentEvent):
    event_type: str = "p2p_gossip"
    peer_address: Tuple[str, int]
    sender_agent_id: str
    gossip_data: Dict[str, Any] # e.g., agent status, known threats

class P2PAlertEvent(AgentEvent):
    event_type: str = "p2p_alert"
    peer_address: Tuple[str, int]
    sender_agent_id: str
    alert_details: Dict[str, Any]

class AgentRegistrationEvent(AgentEvent):
    event_type: str = "agent_registration"
    registration_status: str # e.g., "success", "failed"
    manager_response: Dict[str, Any] # Full response from manager
    public_key_pem: str
    cert_pem: Optional[str] = None # Signed cert received from manager

class AIAnalysisResult(BaseModel):
    """
    Structured result of the AI analysis pipeline for a given event.
    """
    event_id: str
    status: str = "success" # "success", "failed", "simulated"
    reason: Optional[str] = None # Reason for failure or simulation
    initial_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    inferred_context: List[str] = Field(default_factory=list)
    context_confidence: float = 0.0
    ti_matches: List[Dict[str, Any]] = Field(default_factory=list)
    matched_ttps: List[str] = Field(default_factory=list)
    graph_enrichment_findings: List[str] = Field(default_factory=list)
    risk_score: float = 0.0 # Normalized score between 0.0 and 1.0
    risk_factors: List[str] = Field(default_factory=list)
    attributed_to: str = "Unknown"
    attribution_confidence: float = 0.0

class NormalizedEvent(AgentEvent):
    """
    Represents an event after it has been normalized by the orchestrator.
    It includes enrichment from AI analysis.
    """
    # Inherits agent_id, timestamp, event_type, payload from AgentEvent
    # Add fields to store AI analysis results directly
    ai_analysis_result: Optional[AIAnalysisResult] = None

