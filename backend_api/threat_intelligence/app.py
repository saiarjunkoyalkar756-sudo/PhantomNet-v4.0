from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging
import json
import os

from .feed_parser import update_feeds

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

THREAT_DATA_FILE = os.path.join(os.path.dirname(__file__), "threat_data.json")


class IOC(BaseModel):
    type: str  # e.g., "ip", "domain", "hash"
    value: str
    source: str


@app.on_event("startup")
async def startup_event():
    logger.info("Threat Intelligence service starting up...")
    if not os.path.exists(THREAT_DATA_FILE):
        with open(THREAT_DATA_FILE, "w") as f:
            json.dump({"iocs": []}, f)
    # Start a background task to update feeds periodically
    background_tasks = BackgroundTasks()
    background_tasks.add_task(update_feeds, THREAT_DATA_FILE)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Threat Intelligence service is healthy"}


@app.get("/iocs")
async def get_iocs():
    if not os.path.exists(THREAT_DATA_FILE):
        raise HTTPException(
            status_code=404,
            detail="Threat data not found. Please trigger a feed update.",
        )
    with open(THREAT_DATA_FILE, "r") as f:
        threat_data = json.load(f)
    return threat_data


@app.get("/iocs/{ioc_value}")
async def get_ioc(ioc_value: str):
    if not os.path.exists(THREAT_DATA_FILE):
        raise HTTPException(status_code=404, detail="Threat data not found.")
    with open(THREAT_DATA_FILE, "r") as f:
        threat_data = json.load(f)
    for ioc in threat_data.get("iocs", []):
        if ioc.get("value") == ioc_value:
            return ioc
    raise HTTPException(status_code=404, detail="IOC not found")
