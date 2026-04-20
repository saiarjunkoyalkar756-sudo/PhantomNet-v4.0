# backend_api/soar_engine/models.py

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid

class PlaybookStatus(str, Enum):
    """Status of a playbook step or overall execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_APPROVAL = "requires_approval"

class RemediationAction(str, Enum):
    """Types of automated remediation actions."""
    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    KILL_PROCESS = "kill_process"
    CONTAIN_CONTAINER = "contain_container"
    REMOVE_FILE = "remove_file"
    RESET_PASSWORD = "reset_password"
    CREATE_TICKET = "create_ticket"
    NOTIFY_USER = "notify_user"
    ENRICH_INDICATOR = "enrich_indicator" # From Threat Intel Service
    CUSTOM_SCRIPT = "custom_script"
    DISPATCH_AGENT_COMMAND = "dispatch_agent_command"
    TEMPORAL_ROLLBACK = "temporal_rollback"
    TEMPORAL_SNAPSHOT = "temporal_snapshot"

class PlaybookStep(BaseModel):
    """Defines a single step within a SOAR playbook."""
    action: RemediationAction = Field(..., description="The action to perform.")
    tool_name: Optional[str] = Field(None, description="The external tool or system to use (e.g., EDR, Firewall, TicketingSystem, ThreatIntel).")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action, can contain context variables like {incident.ip}.")
    condition: Optional[str] = Field(None, description="Jinja2-like expression to evaluate if this step should run.")
    description: Optional[str] = Field(None, description="Human-readable description of the step.")
    output_to: Optional[str] = Field(None, description="Key in context to store this step's output.")
    requires_approval: bool = Field(False, description="Whether this step requires human approval before execution.")

class Playbook(BaseModel):
    """Represents a SOAR playbook."""
    name: str = Field(..., description="Unique name of the playbook.")
    description: Optional[str] = Field(None, description="Description of what the playbook does.")
    trigger: Dict[str, Any] = Field(..., description="Criteria that trigger this playbook (e.g., {'event_type': 'malware_alert'}).")
    steps: List[PlaybookStep] = Field(..., description="Ordered list of steps to execute.")
    context: Dict[str, Any] = Field(default_factory=dict, description="Initial context variables for the playbook execution.")
    version: str = Field("1.0.0", description="Version of the playbook.")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PlaybookExecutionLog(BaseModel):
    """Log entry for a single step's execution within a playbook run."""
    step_action: RemediationAction
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: PlaybookStatus
    details: str
    output: Dict[str, Any] = Field(default_factory=dict)
    
class PlaybookRun(BaseModel):
    """Represents a single execution instance of a playbook."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for this playbook run.")
    playbook_name: str
    triggered_by: Dict[str, Any] = Field(..., description="The event or incident that triggered this run.")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: PlaybookStatus = PlaybookStatus.PENDING # Overall status of the playbook run
    execution_logs: List[PlaybookExecutionLog] = Field(default_factory=list)
    current_context: Dict[str, Any] = Field(default_factory=dict) # Dynamic context during execution
    
# Example usage:
if __name__ == "__main__":
    import uuid
    print("Playbook models defined:")
    print(Playbook.model_json_schema(indent=2))
    print(PlaybookRun.model_json_schema(indent=2))
