from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
import uuid # Import uuid

import time


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    role: Optional[str] = "user"


class UserInDB(UserBase):
    id: int
    tenant_id: uuid.UUID # New tenant_id field
    hashed_password: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    twofa_enabled: bool = False
    twofa_enforced: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None
    recovery_code: Optional[str] = None  # Add recovery_code to login request
    device_fingerprint: Optional[str] = None  # Add device_fingerprint


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class RecoveryCodeResponse(BaseModel):
    codes: list[str]


class TwoFACode(BaseModel):
    code: str


class TwoFAChallenge(BaseModel):
    challenge_id: str
    code: Optional[str] = None
    recovery_code: Optional[str] = None


class MFARequiredResponse(BaseModel):
    mfa_required: bool = True
    challenge_id: str


class SecurityAlert(BaseModel):
    timestamp: str
    ip_address: str
    risk_level: str
    message: str
    # Add other relevant fields like user_id, session_id, etc., as needed


class Webhook(BaseModel):
    url: str
    events: list[str]


class AttackSimulation(BaseModel):
    data: str


class AgentRegistration(BaseModel):
    public_key: str
    role: str
    version: str
    location: str
    bootstrap_token: Optional[str] = None


class BootstrapToken(BaseModel):
    token: str


class AgentKeyPair(BaseModel):
    private_key: str
    public_key: str


class SecurityEvent(BaseModel):
    event_data: dict
    originating_agent_id: int
    agent_signature: str
    receiving_node_id: Optional[int] = None
    node_attestation: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    previous_event_hash: Optional[str] = None
    event_hash: Optional[str] = None


class AgentHeartbeat(BaseModel):
    status: str
    metrics: dict
    trust_delta: float
    os: Optional[str] = None # OS of the agent
    capabilities: Optional[Dict[str, Any]] = None # Capabilities of the agent
    # New fields for self-healing
    health_metrics: Optional[Dict[str, Any]] = None # Detailed health snapshot
    recent_errors: Optional[List[Dict[str, Any]]] = None # Recently detected errors
    self_healing_active: Optional[bool] = None # Is self-healing controller active
    safe_mode_active: Optional[bool] = None # Is agent in safe mode

class AgentConfiguration(BaseModel):
    """Configuration parameters for a PhantomNet Agent."""
    reporting_interval_seconds: int = 300 # How often the agent sends telemetry/heartbeats
    enabled_modules: List[str] = ["telemetry_collector", "health_monitor"] # List of modules to run
    log_sources: List[str] = ["syslog", "auth_logs", "process_activity"] # Log sources to monitor
    telemetry_level: str = "medium" # e.g., "low", "medium", "high"
    policy_version: Optional[str] = None # Version of the policy currently applied to the agent
    # Add other configuration parameters as needed

class AgentRegistration(BaseModel):
    public_key: str
    role: str
    version: str
    location: str
    bootstrap_token: Optional[str] = None
    configuration: Optional[AgentConfiguration] = None # New: Optional initial configuration
    os: Optional[str] = None # OS of the agent registering
    capabilities: Optional[Dict[str, Any]] = None # Capabilities of the agent registering
    self_healing_enabled: Optional[bool] = None # Is self-healing enabled on this agent
    safe_mode_active: Optional[bool] = None # Is the agent starting in safe mode


class GossipMessage(BaseModel):
    trust_map: dict[int, float]

# Assuming a basic event model
class RawEvent(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique event ID"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Unix timestamp of the event"
    )
    source: str = Field(
        ...,
        description="Source of the event (e.g., 'BlueTeamAI', 'SensorX', 'Syslog', 'Filebeat')",
    )
    type: str = Field(
        ...,
        description="Type of event (e.g., 'traffic_anomaly', 'login_attempt', 'syslog', 'audit')",
    )
    agent_id: Optional[str] = Field(None, description="ID of the agent that sent the event")
    agent_os: Optional[str] = Field(None, description="Operating system of the agent")
    agent_capabilities: Optional[Dict[str, Any]] = Field(None, description="Capabilities of the agent's OS")
    data: Dict[str, Any] = Field(
        {}, description="Raw event data parsed into key-value pairs"
    )
    raw_log: Optional[str] = Field(
        None, description="Original raw log string, if applicable"
    )


class CorrelatedEvent(RawEvent):
    correlation_id: str = Field(..., description="ID linking correlated events")
    related_events: List[str] = Field([], description="List of IDs of related events")
    severity: str = Field(..., description="Overall severity of the correlated event")
    ai_score: float = Field(
        ..., ge=0, le=1.0, description="AI-driven correlation score"
    )
    action_recommendation: Optional[str] = Field(
        None, description="Recommended action from AI"
    )

class NormalizedEvent(BaseModel):
    event_id: str
    timestamp: float
    source: str
    event_type: str
    raw_data: str
    metadata: Dict[str, Any]
    host_name: Optional[str] = None
    user_name: Optional[str] = None
    src_ip: Optional[str] = None


class TransactionData(BaseModel):
    ip: str = Field(..., description="IP address of the attacking entity")
    port: int = Field(
        ..., ge=1, le=65535, description="Port number involved in the attack"
    )
    data: str = Field(
        ..., min_length=1, max_length=2048, description="Raw attack data or payload"
    )

    @field_validator("ip")
    def validate_ip_address(cls, v):
        # Basic IP address validation (can be expanded for IPv6 or more strict checks)
        parts = v.split(".")
        if len(parts) != 4 or not all(
            part.isdigit() and 0 <= int(part) <= 255 for part in parts
        ):
            raise ValueError("Invalid IP address format")
        return v


class HoneypotControl(BaseModel):
    action: str = Field(..., description="Action to perform: 'start' or 'stop'")
    port: int = Field(..., ge=1, le=65535, description="Port number for the honeypot")


class SimulateAttack(BaseModel):
    ip: str = Field(..., description="IP address for simulation")
    port: int = Field(..., ge=1, le=65535, description="Port for simulation")
    data: str = Field(..., min_length=1, description="Raw data for simulation")

