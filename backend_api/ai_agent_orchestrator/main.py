from backend_api.shared.service_factory import create_phantom_service
from .agent_brain import AgentBrain
from loguru import logger
from typing import Dict, Any, List, Optional
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = create_phantom_service(
    name="AI Agent Orchestrator",
    description="The central nervous system for autonomous security agents.",
    version="1.0.0"
)

# --- Models ---
class TaskRequest(BaseModel):
    task_description: str
    context: Optional[Dict[str, Any]] = None
    agent_persona: str = "sentinel" # sentinel, recon, forensic

class TaskResponse(BaseModel):
    task_id: str
    status: str
    reasoning_steps: List[str]
    proposed_actions: List[Dict[str, Any]]

# --- Initialize Brain ---
brain = AgentBrain()

@app.post("/agents/task")
async def submit_task(request: TaskRequest):
    """
    Submits a natural language task to the AI Agent swarm.
    """
    logger.info(f"AI Agent ({request.agent_persona}) received task: {request.task_description}")
    
    try:
        result = await brain.reason_and_plan(
            task=request.task_description,
            persona=request.agent_persona,
            context=request.context or {}
        )
        return success_response(data=result)
    except Exception as e:
        logger.error(f"Agent reasoning failed: {e}")
        return error_response(code="AGENT_REASONING_FAILED", message=str(e), status_code=500)
