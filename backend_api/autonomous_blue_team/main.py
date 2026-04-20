from backend_api.shared.service_factory import create_phantom_service
from .consumer import start_kafka_consumer
from loguru import logger
from pydantic import BaseModel
import asyncio
import uuid
import os
import json
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request

ACTION_HISTORY_DIR = os.getenv("ACTION_HISTORY_DIR", "/tmp/action_history")

async def blue_team_startup(app: FastAPI):
    """
    Handles startup events for the Autonomous Blue Team application.
    """
    if not os.path.exists(ACTION_HISTORY_DIR):
        os.makedirs(ACTION_HISTORY_DIR)
        logger.info(f"Autonomous Blue Team: Created directory {ACTION_HISTORY_DIR}")
    
    # Start the Kafka consumer as a background task
    app.state.consumer_task = asyncio.create_task(start_kafka_consumer())
    logger.info("Autonomous Blue Team: Kafka consumer task started.")

async def blue_team_shutdown(app: FastAPI):
    if hasattr(app.state, "consumer_task"):
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Autonomous Blue Team: Kafka consumer task stopped.")

app = create_phantom_service(
    name="Autonomous Blue Team",
    description="Automated defensive actions and containment.",
    version="1.0.0",
    custom_startup=blue_team_startup,
    custom_shutdown=blue_team_shutdown
)

class DefensiveActionRequest(BaseModel):
    action_type: str
    target: str
    reason: str
    alert_id: str

@app.post("/take_action")
async def take_defensive_action(request: DefensiveActionRequest, background_tasks: BackgroundTasks):
    action_id = str(uuid.uuid4())
    # Deployment of actual defensive logic...
    return success_response(data={"action_id": action_id, "status": "initiated"}, message="Defensive action initiated.")

@app.get("/action_history/{action_id}")
async def get_action_history(action_id: str):
    result_file = os.path.join(ACTION_HISTORY_DIR, f"{action_id}.json")
    if not os.path.exists(result_file):
        return error_response(code="NOT_FOUND", message="Action history not found.", status_code=404)
    
    with open(result_file, "r") as f:
        history = json.load(f)
    return success_response(data=history)

@app.get("/action_list")
async def get_action_list():
    actions = []
    if os.path.exists(ACTION_HISTORY_DIR):
        for filename in os.listdir(ACTION_HISTORY_DIR):
            if filename.endswith(".json"):
                actions.append(filename.replace(".json", ""))
    return success_response(data={"actions": actions})
