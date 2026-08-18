"""Authorized command dispatch for endpoint agents.

The service records an audit event before publishing a command. If audit publication fails,
the command is not dispatched. Endpoint execution must independently emit its final outcome.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from kafka import KafkaProducer
from loguru import logger
from pydantic import BaseModel, Field

from backend_api.core.response import success_response
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User


router = APIRouter(prefix="/api/v1/agents", tags=["Agent Commands"])

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")
AGENT_COMMANDS_TOPIC = "agent-commands"
AUDIT_EVENTS_TOPIC = "audit-events"
AUDIT_PUBLISH_TIMEOUT_SECONDS = 5

producer: KafkaProducer | None = None


def get_kafka_producer() -> KafkaProducer:
    """Lazily create the broker client so imports never initiate network activity."""
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
    return producer


class AgentCommandPayload(BaseModel):
    command_type: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None


class NetworkActionPayload(BaseModel):
    action: str
    agent_id: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _command_data(
    current_user: User,
    target_agent_id: str,
    command_type: str,
    arguments: Dict[str, Any],
    task_id: Optional[str],
) -> Dict[str, Any]:
    return {
        "tenant_id": str(current_user.tenant_id),
        "target_agent_id": target_agent_id,
        "command_type": command_type,
        "arguments": arguments,
        "task_id": task_id or str(uuid4()),
        "issued_by": current_user.username,
        "issued_at": _utc_now(),
    }


def _audit_event(command_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_type": "agent.command.requested",
        "tenant_id": command_data["tenant_id"],
        "actor_id": command_data["issued_by"],
        "target_agent_id": command_data["target_agent_id"],
        "command_type": command_data["command_type"],
        "task_id": command_data["task_id"],
        "timestamp": command_data["issued_at"],
        "status": "requested",
    }


def _publish_required_audit(producer_client: KafkaProducer, command_data: Dict[str, Any]) -> None:
    """Persist an intent event before command dispatch or fail the request closed."""
    future = producer_client.send(AUDIT_EVENTS_TOPIC, _audit_event(command_data))
    future.get(timeout=AUDIT_PUBLISH_TIMEOUT_SECONDS)


def _publish_command(producer_client: KafkaProducer, command_data: Dict[str, Any]) -> None:
    future = producer_client.send(AGENT_COMMANDS_TOPIC, command_data)
    future.get(timeout=AUDIT_PUBLISH_TIMEOUT_SECONDS)


async def _dispatch_authorized_command(command_data: Dict[str, Any]) -> None:
    try:
        producer_client = get_kafka_producer()
        _publish_required_audit(producer_client, command_data)
        _publish_command(producer_client, command_data)
    except Exception as exc:
        logger.error(
            "Command dispatch failed; the command was not accepted",
            task_id=command_data["task_id"],
            target_agent_id=command_data["target_agent_id"],
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Command dispatch unavailable; no command was accepted",
        ) from exc


@router.post("/{agent_id}/command", status_code=status.HTTP_202_ACCEPTED)
async def send_agent_command(
    agent_id: str,
    command: AgentCommandPayload,
    current_user: User = Depends(require_capability("agents:command")),
):
    """Audit and dispatch a requested endpoint command for an authorized operator."""
    command_data = _command_data(
        current_user=current_user,
        target_agent_id=agent_id,
        command_type=command.command_type,
        arguments=command.arguments,
        task_id=command.task_id,
    )
    await _dispatch_authorized_command(command_data)
    logger.info("Agent command accepted", **command_data)
    return success_response(data={"message": "Command accepted", "task_id": command_data["task_id"]})


@router.post("/network/action", status_code=status.HTTP_202_ACCEPTED)
async def send_network_action(
    payload: NetworkActionPayload,
    current_user: User = Depends(require_capability("agents:command")),
):
    """Audit and dispatch an authorized network action through the agent command topic."""
    command_data = _command_data(
        current_user=current_user,
        target_agent_id=payload.agent_id,
        command_type=payload.action,
        arguments=payload.arguments,
        task_id=payload.task_id,
    )
    await _dispatch_authorized_command(command_data)
    logger.info("Network action accepted", **command_data)
    return success_response(data={"message": "Network action accepted", "task_id": command_data["task_id"]})
