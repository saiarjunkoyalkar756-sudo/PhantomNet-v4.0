from fastapi import FastAPI, BackgroundTasks, HTTPException
import logging
import json
import os
import time

from .mapper import load_mitre_data, map_event_to_techniques

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

MITRE_DATA_FILE = os.path.join(os.path.dirname(__file__), "mitre_data.json")


@app.on_event("startup")
async def startup_event():
    logger.info("MITRE ATT&CK Mapper service starting up...")
    # Load MITRE data on startup
    load_mitre_data(MITRE_DATA_FILE)
    logger.info("MITRE data loaded.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "MITRE ATT&CK Mapper service is healthy"}


@app.get("/techniques")
async def get_techniques():
    if not os.path.exists(MITRE_DATA_FILE):
        raise HTTPException(
            status_code=404,
            detail="MITRE data not found. Please ensure data is loaded.",
        )
    with open(MITRE_DATA_FILE, "r") as f:
        mitre_data = json.load(f)
    return {"techniques": mitre_data.get("techniques", [])}


@app.post("/map_event")
async def map_event(event: dict):
    logger.info(
        f"Mapping event to MITRE ATT&CK techniques: {event.get('event_id', 'N/A')}"
    )
    mapped_techniques = map_event_to_techniques(event, MITRE_DATA_FILE)
    return {"event": event, "mapped_techniques": mapped_techniques}
