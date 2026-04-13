# api/control_api.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime # Import datetime for timestamp
import uuid # For generating unique command IDs

from core.state import get_agent_state
from orchestrator import Orchestrator # Import Orchestrator to ingest commands
from schemas.actions import AgentCommand # Import the AgentCommand schema (will be defined in next task)
# from security.auth import verify_api_key # Assuming an auth module for API key verification

router = APIRouter()

# No longer needed, as we will use AgentCommand directly and FastAPI's JSONResponse
# class AgentCommandRequest(BaseModel):
#     command_type: str
#     payload: Dict[str, Any] = {}

@router.post("/control/collector/{collector_name}/start", status_code=200)
async def start_collector(collector_name: str): #, api_key: str = Depends(verify_api_key)):
    """
    Starts a specific collector by name.
    """
    agent_state = get_agent_state()
    if collector_name not in agent_state.collectors:
        raise HTTPException(status_code=404, detail=f"Collector '{collector_name}' not found.")
    
    collector = agent_state.collectors[collector_name]
    if getattr(collector, 'running', False):
        return {"status": "success", "message": f"Collector '{collector_name}' is already running."}
    
    try:
        await collector.start()
        return {"status": "success", "message": f"Collector '{collector_name}' started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start collector '{collector_name}': {e}")

@router.post("/control/collector/{collector_name}/stop", status_code=200)
async def stop_collector(collector_name: str): #, api_key: str = Depends(verify_api_key)):
    """
    Stops a specific collector by name.
    """
    agent_state = get_agent_state()
    if collector_name not in agent_state.collectors:
        raise HTTPException(status_code=404, detail=f"Collector '{collector_name}' not found.")
    
    collector = agent_state.collectors[collector_name]
    if not getattr(collector, 'running', False):
        return {"status": "success", "message": f"Collector '{collector_name}' is already stopped."}
    
    try:
        await collector.stop()
        return {"status": "success", "message": f"Collector '{collector_name}' stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop collector '{collector_name}': {e}")

@router.post("/control/plugins/reload", status_code=200)
async def reload_plugins(): #, api_key: str = Depends(verify_api_key)):
    """
    Reloads all plugins.
    """
    # This would typically involve re-initializing the PluginLoader and re-loading plugins.
    # For now, it's a placeholder.
    # The actual implementation would need access to the PluginLoader instance,
    # likely passed via dependency injection or a global agent context.
    return {"status": "success", "message": "Plugin reload initiated (placeholder)."}

@router.post("/agent/command", status_code=202)
async def post_agent_command(command_request: AgentCommand): #, api_key: str = Depends(verify_api_key)):
    """
    Receives commands for the agent and ingests them into the orchestrator for processing.
    """
    agent_state = get_agent_state()
    orchestrator: Orchestrator = agent_state.orchestrator # Assuming orchestrator is stored in agent_state

    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized in agent state.")

    command_id = str(uuid.uuid4())
    command_event = {
        "event_type": "AGENT_COMMAND_FROM_UI", # Differentiate from bus commands
        "command_id": command_id,
        "command_type": command_request.command_type,
        "payload": command_request.payload.model_dump() if hasattr(command_request.payload, 'model_dump') else command_request.payload,
        "timestamp": datetime.now().isoformat(),
        "source": "ui_console"
    }
    await orchestrator.ingest_event(command_event)
    
    return {
        "status": "accepted",
        "message": f"Command '{command_request.command_type}' accepted for processing by Orchestrator.",
        "command_id": command_id
    }

@router.get("/agent/commands/status/{command_id}", status_code=200)
async def get_command_status(command_id: str): #, api_key: str = Depends(verify_api_key)):
    """
    Returns the current status of a previously issued command.
    # TODO: Implement actual command status tracking in agent_state or a dedicated CommandManager.
    """
    # For now, return a mock status
    return {
        "command_id": command_id,
        "status": "processing", # Mock status
        "message": "Command status tracking is not yet fully implemented. Returning mock status.",
        "details": {}
    }


