from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .scanner import run_scan
from .database import create_assets_table, get_all_assets
from loguru import logger
import os
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

class ScanRequest(BaseModel):
    target: str

async def asset_inventory_startup(app: FastAPI):
    """
    Handles startup events for the Asset Inventory service.
    """
    create_assets_table()
    logger.info("Asset Inventory: Database tables initialized.")

app = create_phantom_service(
    name="Asset Inventory Service",
    description="Maintains a record of discovered assets.",
    version="1.0.0",
    custom_startup=asset_inventory_startup
)

@app.post("/scan")
async def start_asset_scan(scan_request: ScanRequest, background_tasks: BackgroundTasks):
    logger.info(f"Starting scan for target: {scan_request.target}")
    background_tasks.add_task(run_scan, scan_request.target)
    return success_response(message="Scan initiated in the background.")

@app.get("/assets")
async def get_assets():
    assets = get_all_assets()
    return success_response(data=assets)
