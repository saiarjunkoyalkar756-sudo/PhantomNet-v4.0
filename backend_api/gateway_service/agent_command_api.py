from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from kafka import KafkaProducer
import json
import os
from uuid import UUID
import logging

from iam_service.auth_methods import get_current_user, has_role, UserRole
from shared.database import User # Import User model

logger = logging.getLogger("phantomnet_gateway.agent_command_api")

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agent Commands"],
)

# --- Kafka Producer Setup ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
AGENT_COMMANDS_TOPIC = 'agent-commands'

producer = None
def get_kafka_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return producer

# --- Pydantic Models ---
class AgentCommandPayload(BaseModel):
    command_type: str # e.g., "kill_process", "get_file", "run_script"
    arguments: Dict[str, Any] = {} # Arguments for the command
    task_id: Optional[str] = None # Unique ID for tracking command status

@router.post("/{agent_id}/command", status_code=status.HTTP_202_ACCEPTED)
async def send_agent_command(
    agent_id: str,
    command: AgentCommandPayload,
    current_user: User = Depends(has_role([UserRole.ADMIN, UserRole.ANALYST])) # RBAC
):
    """
    Sends a command to a specific agent via the Kafka agent-commands topic.
    """
    # Ensure the command includes tenant_id for multi-tenancy
    command_data = {
        "tenant_id": str(current_user.tenant_id),
        "target_agent_id": agent_id,
        "command_type": command.command_type,
        "arguments": command.arguments,
        "task_id": command.task_id if command.task_id else str(uuid.uuid4()),
        "issued_by": current_user.username,
        "issued_at": datetime.now().isoformat()
    }

    try:
        kafka_producer = get_kafka_producer()
        kafka_producer.send(AGENT_COMMANDS_TOPIC, command_data)
        logger.info(f"Command '{command_data['command_type']}' for agent {agent_id} issued by {current_user.username}", extra=command_data)
        return {"status": "Command accepted", "task_id": command_data['task_id']}
    except Exception as e:
        logger.error(f"Failed to send command to agent {agent_id}: {e}", exc_info=True, extra=command_data)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send command")

