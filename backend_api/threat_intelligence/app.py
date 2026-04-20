from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
import asyncio
import json
import os
from loguru import logger
from .feed_parser import update_feeds

THREAT_DATA_FILE = os.path.join(os.path.dirname(__file__), "threat_data.json")

class IOC(BaseModel):
    type: str  # e.g., "ip", "domain", "hash"
    value: str
    source: str

async def threat_intel_startup(app: FastAPI):
    """
    Handles startup events for the Threat Intelligence Service.
    """
    if not os.path.exists(THREAT_DATA_FILE):
        with open(THREAT_DATA_FILE, "w") as f:
            json.dump({"iocs": []}, f)
    
    # Start feed update in background
    # Note: In production, this would be a scheduled cron or celery task
    asyncio.create_task(update_feeds(THREAT_DATA_FILE))
    logger.info("Threat Intelligence: Background feed update started.")

app = create_phantom_service(
    name="Threat Intelligence Service",
    description="Aggregates and serves IOCs from various threat feeds.",
    version="1.0.0",
    custom_startup=threat_intel_startup
)

@app.get("/iocs")
async def get_iocs():
    if not os.path.exists(THREAT_DATA_FILE):
        return error_response(code="DATA_NOT_FOUND", message="Threat data not initialized.", status_code=404)
    
    with open(THREAT_DATA_FILE, "r") as f:
        threat_data = json.load(f)
    return success_response(data=threat_data)

@app.get("/iocs/{ioc_value}")
async def get_ioc(ioc_value: str):
    if not os.path.exists(THREAT_DATA_FILE):
        return error_response(code="DATA_NOT_FOUND", message="Threat data not found.", status_code=404)
    
    with open(THREAT_DATA_FILE, "r") as f:
        threat_data = json.load(f)
    
    for ioc in threat_data.get("iocs", []):
        if ioc.get("value") == ioc_value:
            return success_response(data=ioc)
            
    return error_response(code="IOC_NOT_FOUND", message=f"IOC {ioc_value} not found.", status_code=404)
