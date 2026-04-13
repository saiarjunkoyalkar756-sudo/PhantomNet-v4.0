from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging
import threading
import json
import os
import time
import uuid

import asyncio
from .consumer import start_kafka_consumer
...
@app.on_event("startup")
async def startup_event():
    logger.info("Autonomous Blue Team Engine starting up...")
    # Start the Kafka consumer as a background task
    asyncio.create_task(start_kafka_consumer())
    logger.info("Kafka consumer for Autonomous Blue Team started.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Autonomous Blue Team Engine is healthy"}


@app.post("/take_action")
async def take_defensive_action(
    request: DefensiveActionRequest, background_tasks: BackgroundTasks
):
    action_id = str(uuid.uuid4())
    logger.info(
        f"Initiating defensive action: {request.action_type} (ID: {action_id}) on target: {request.target}"
    )

    result_file = os.path.join(ACTION_HISTORY_DIR, f"{action_id}.json")

    # Map action type to function
    action_func = None
    if request.action_type == "auto_block_ip":
        action_func = auto_block_ip
    elif request.action_type == "auto_isolate_host":
        action_func = auto_isolate_host
    elif request.action_type == "auto_reverse_changes":
        action_func = auto_reverse_changes
    elif request.action_type == "auto_kill_process":
        action_func = auto_kill_process
    elif request.action_type == "auto_lock_account":
        action_func = auto_lock_account
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown defensive action type: {request.action_type}",
        )

    background_tasks.add_task(
        action_func,
        action_id,
        request.target,
        request.reason,
        request.alert_id,
        result_file,
    )
    return {
        "message": "Defensive action initiated in the background.",
        "action_id": action_id,
    }


@app.get("/action_history/{action_id}")
async def get_action_history(action_id: str):
    result_file = os.path.join(ACTION_HISTORY_DIR, f"{action_id}.json")
    if not os.path.exists(result_file):
        raise HTTPException(
            status_code=404,
            detail="Action history not found. May still be in progress.",
        )
    with open(result_file, "r") as f:
        history = json.load(f)
    return history


@app.get("/action_list")
async def get_action_list():
    actions = []
    for filename in os.listdir(ACTION_HISTORY_DIR):
        if filename.endswith(".json"):
            action_id = filename.replace(".json", "")
            actions.append(action_id)
    return {"actions": actions}
