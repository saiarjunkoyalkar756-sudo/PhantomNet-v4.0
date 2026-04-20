from backend_api.shared.service_factory import create_phantom_service
from .mapper import load_mitre_data, map_event_to_techniques
from loguru import logger
import asyncio
import os
import json
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException, Request

MITRE_DATA_FILE = os.path.join(os.path.dirname(__file__), "mitre_data.json")

async def mapper_startup(app: FastAPI):
    # Startup tasks
    if os.path.exists(MITRE_DATA_FILE):
        load_mitre_data(MITRE_DATA_FILE)
        logger.info("MITRE ATT&CK Mapper: Data loaded successfully.")
    else:
        logger.warning(f"MITRE ATT&CK Mapper: Data file {MITRE_DATA_FILE} not found.")

app = create_phantom_service(
    name="MITRE ATT&CK Mapper",
    description="Maps security events to MITRE ATT&CK techniques.",
    version="1.0.0",
    custom_startup=mapper_startup
)

@app.get("/techniques")
async def get_techniques():
    if not os.path.exists(MITRE_DATA_FILE):
        return error_response(code="NOT_FOUND", message="MITRE data file missing", status_code=404)
    with open(MITRE_DATA_FILE, "r") as f:
        mitre_data = json.load(f)
    return success_response(data={"techniques": mitre_data.get("techniques", [])})

@app.post("/map_event")
async def map_event(event: dict):
    mapped_techniques = map_event_to_techniques(event, MITRE_DATA_FILE)
    return success_response(data={"event": event, "mapped_techniques": mapped_techniques})
