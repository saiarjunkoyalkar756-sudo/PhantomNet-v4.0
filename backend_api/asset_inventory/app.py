from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging
import json
import os
from datetime import datetime

from .scanner import run_scan
from .database import create_assets_table, get_all_assets

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


class ScanRequest(BaseModel):
    target: str  # e.g., "192.168.1.0/24"


@app.on_event("startup")
async def startup_event():
    logger.info("Asset Inventory service starting up...")
    create_assets_table()


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Asset Inventory service is healthy"}


@app.post("/scan")
async def start_asset_scan(
    scan_request: ScanRequest, background_tasks: BackgroundTasks
):
    logger.info(f"Starting scan for target: {scan_request.target}")
    background_tasks.add_task(run_scan, scan_request.target)
    return {"message": "Scan initiated in the background."}


@app.get("/assets")
async def get_assets():
    assets = get_all_assets()
    return {"assets": assets}
