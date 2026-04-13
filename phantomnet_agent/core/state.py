from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import socket
import logging

from shared.platform_utils import get_platform_details, IS_WINDOWS, IS_LINUX, IS_TERMUX, IS_ROOT, HAS_PCAP, HAS_EBPF, CAN_BIND_LOW_PORTS, ARCH, PLATFORM_INFO, SAFE_MODE

logger = logging.getLogger("phantomnet_agent.core.state")

class ComponentHealth(BaseModel):
    """Model to track the health status of individual agent components."""
    status: str = "unknown" # e.g., "running", "stopped", "degraded", "error"
    details: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

class AgentState(BaseModel):
    """
    A Pydantic model to hold and manage the agent's runtime state,
    including its identity, operational status, and health of its components.
    """
    agent_id: str
    mode: str
    version: str = "0.0.1" # Agent version
    hostname: str = "unknown"
    os: str = "unknown" # Will be set by os_adapter
    capabilities: Dict[str, Any] = Field(default_factory=dict) # Store platform capabilities
    started_at: datetime = Field(default_factory=datetime.now)
    status: str = "initializing" # Overall agent status: "initializing", "running", "degraded", "stopped", "error"
    bus_connected: bool = False
    last_heartbeat: datetime = Field(default_factory=datetime.now) # Timestamp of last reported heartbeat
    config: Any = None # Store the entire agent configuration
    cert_path: Optional[str] = None # Path to the agent's signed certificate
    key_path: Optional[str] = None # Path to the agent's private key
    jwt_manager: Any = None # Store the JWTManager instance
    
    # Store instances of collectors and plugins, which can be queried for their internal state
    collectors: Dict[str, Any] = Field(default_factory=dict) # Stores collector instances
    plugins: Dict[str, Any] = Field(default_factory=dict)   # Stores loaded plugin instances
    
    # Track health of various components using the ComponentHealth model
    component_health: Dict[str, ComponentHealth] = Field(default_factory=dict)
    
    orchestrator: Any = None # Reference to the Orchestrator instance

    def update_component_health(self, name: str, status: str, details: Optional[Dict[str, Any]] = None):
        """
        Updates the health status of a specific agent component.
        """
        current_details = self.component_health.get(name, ComponentHealth()).details
        if details:
            current_details.update(details) # Merge new details
        self.component_health[name] = ComponentHealth(
            status=status, 
            details=current_details, 
            last_updated=datetime.now()
        )
        logger.debug(f"Updated health for component '{name}': status='{status}'")

    def get_health_snapshot(self) -> Dict[str, Any]:
        """
        Returns a snapshot of the agent's overall health and component-specific health.
        Converts datetime objects to ISO format strings for JSON serialization.
        """
        # Use model_dump to get a serializable dict, and then process datetime fields
        snapshot = self.model_dump(exclude={'collectors', 'plugins', 'orchestrator', 'config', 'jwt_manager'})

        # Convert top-level datetime fields in snapshot
        if 'started_at' in snapshot and isinstance(snapshot['started_at'], datetime):
            snapshot['started_at'] = snapshot['started_at'].isoformat()
        if 'last_heartbeat' in snapshot and isinstance(snapshot['last_heartbeat'], datetime):
            snapshot['last_heartbeat'] = snapshot['last_heartbeat'].isoformat()

        # Process component_health
        processed_component_health = {}
        for name, health in self.component_health.items():
            health_dict = health.model_dump()
            if 'last_updated' in health_dict and isinstance(health_dict['last_updated'], datetime):
                health_dict['last_updated'] = health_dict['last_updated'].isoformat()
            # If 'details' can contain datetime, it needs recursive processing
            # For now, assuming 'details' is already JSON-serializable or will be handled by json.dumps default()
            processed_component_health[name] = health_dict
        snapshot['component_health'] = processed_component_health

        # Add basic info from collectors if available
        collectors_summary = {}
        for name, instance in self.collectors.items():
            collectors_summary[name] = {
                "is_running": getattr(instance, 'running', False),
                "last_collected": getattr(instance, 'last_collected', None).isoformat() if getattr(instance, 'last_collected', None) and isinstance(getattr(instance, 'last_collected', None), datetime) else getattr(instance, 'last_collected', None),
                "status": getattr(instance, 'status', 'N/A')
            }
        snapshot['collectors_summary'] = collectors_summary

        return snapshot

# A global instance of the agent state, initialized once
_agent_state: Optional[AgentState] = None

def get_agent_state() -> AgentState:
    """
    Returns the global agent state instance.
    Raises RuntimeError if the state has not been initialized.
    """
    if _agent_state is None:
        raise RuntimeError("Agent state has not been initialized. Call initialize_agent_state first.")
    return _agent_state

def initialize_agent_state(agent_id: str, mode: str, os_type: str, capabilities: Dict[str, Any]) -> AgentState:
    """
    Initializes the global agent state. Can only be called once.
    """
    global _agent_state
    if _agent_state is not None:
        raise RuntimeError("Agent state has already been initialized.")
    
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "unknown"
    
    _agent_state = AgentState(
        agent_id=agent_id,
        mode=mode,
        started_at=datetime.now(),
        hostname=hostname,
        os=os_type, 
        capabilities=capabilities, 
        status="running" # Initial status
    )
    logger.info(f"Agent state initialized for agent '{agent_id}' on '{hostname}' ({os_type}). Capabilities: {capabilities}")
    return _agent_state