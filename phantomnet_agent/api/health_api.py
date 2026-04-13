# api/health_api.py
from fastapi import APIRouter, HTTPException
from core.state import get_agent_state, AgentState, ComponentHealth # Import AgentState and ComponentHealth
from typing import Dict, Any, List

router = APIRouter()

@router.get("/agent/health", response_model=Dict[str, Any])
async def get_agent_health():
    """
    Returns a basic health check of the agent, leveraging AgentState's snapshot.
    """
    agent_state = get_agent_state()
    return agent_state.get_health_snapshot()

@router.get("/agent/status", response_model=Dict[str, Any])
async def get_agent_full_status():
    """
    Returns a detailed status of the agent, including all components' status.
    This is essentially the full health snapshot.
    """
    agent_state = get_agent_state()
    return agent_state.get_health_snapshot()

@router.get("/agent/components", response_model=Dict[str, ComponentHealth])
async def get_agent_components_status():
    """
    Returns the detailed health status of individual agent components.
    """
    agent_state = get_agent_state()
    return agent_state.component_health


