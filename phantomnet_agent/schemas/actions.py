# schemas/actions.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid # For default_factory in command_id

class AgentAction(BaseModel):
    agent_id: str
    action_id: str
    action_type: str
    timestamp: float
    payload: Dict[str, Any]

class ProcessKillAction(AgentAction):
    action_type: str = "process_kill"
    pid: int
    force: bool = False

class NetworkBlockAction(AgentAction):
    action_type: str = "network_block"
    address: str
    port: Optional[int] = None
    protocol: Optional[str] = None # e.g., 'TCP', 'UDP'
    direction: Optional[str] = None # 'inbound', 'outbound'

class SystemIsolateAction(AgentAction):
    action_type: str = "system_isolate"
    duration_seconds: Optional[int] = None
    reason: Optional[str] = None

class AgentCommand(BaseModel):
    """
    Model representing a command issued to the agent, typically from the UI or backend.
    """
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4())) # Unique ID for the command
    command_type: str # e.g. "run_scan", "collect_logs", "ping_host", "restart_collector"
    target: Optional[str] = None # e.g. "collector_name", "host_ip"
    payload: Dict[str, Any] = Field(default_factory=dict) # Parameters for the command
    timestamp: str = Field(default_factory=datetime.now().isoformat)
    source: str = "ui_console" # "ui_console", "backend", "internal"
    status: str = "pending" # "pending", "in_progress", "completed", "failed"
    result: Dict[str, Any] = Field(default_factory=dict) # Result of the command execution

