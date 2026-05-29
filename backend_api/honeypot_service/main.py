# backend_api/honeypot_service/main.py
from fastapi import FastAPI, HTTPException, Response
from typing import List, Dict, Any
import uvicorn
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .manager import honeypot_manager
from .models import HoneypotConfig, HoneypotCreate # Import HoneypotConfig and HoneypotCreate from models.py
from .metrics import honeypot_active_instances # Import metrics

# Initialize FastAPI app
app = FastAPI(
    title="Honeypot Service",
    description="Manages lifecycle and events for honeypots.",
    version="0.1.0",
)

@app.post("/honeypots", response_model=HoneypotConfig, summary="Create and start a new honeypot",
            description="Registers a new honeypot instance with the system and starts its emulation process.")
async def create_honeypot(config: HoneypotCreate):
    if config.honeypot_id in [h.honeypot_id for h in honeypot_manager.list_honeypots()]:
        raise HTTPException(status_code=400, detail="Honeypot ID already exists")

    new_honeypot = HoneypotConfig(**config.dict(), status="stopped", pid=None)
    await honeypot_manager.start_honeypot(new_honeypot)
    # The manager updates the status, so fetch it again
    updated_honeypot = honeypot_manager.get_honeypot_status(new_honeypot.honeypot_id)
    if updated_honeypot and updated_honeypot.status == "running":
        honeypot_active_instances.labels(honeypot_type=updated_honeypot.type).inc()
    return updated_honeypot

@app.get("/honeypots", response_model=List[HoneypotConfig], summary="List all deployed honeypots",
           description="Retrieves a list of all currently registered honeypot instances and their current status.")
async def list_honeypots():
    return honeypot_manager.list_honeypots()

@app.post("/honeypots/{honeypot_id}/stop", response_model=HoneypotConfig, summary="Stop a running honeypot",
             description="Sends a signal to stop a specific honeypot instance identified by its ID.")
async def stop_honeypot(honeypot_id: str):
    honeypot = honeypot_manager.get_honeypot_status(honeypot_id)
    if not honeypot:
        raise HTTPException(status_code=404, detail="Honeypot not found")
    await honeypot_manager.stop_honeypot(honeypot_id)
    updated_honeypot = honeypot_manager.get_honeypot_status(honeypot_id)
    if updated_honeypot and updated_honeypot.status == "stopped":
        honeypot_active_instances.labels(honeypot_type=updated_honeypot.type).dec()
    return updated_honeypot

@app.get("/honeypots/{honeypot_id}/events", response_model=List[Dict[str, Any]], summary="Retrieve captured events for a honeypot",
           description="Fetches a list of events captured by a specific honeypot. (Placeholder: currently returns empty list)")
async def get_honeypot_events(honeypot_id: str):
    if not honeypot_manager.get_honeypot_status(honeypot_id):
        raise HTTPException(status_code=404, detail="Honeypot not found")
    # This is a placeholder. In a real scenario, this would fetch from a database or event stream.
    return []

@app.get("/metrics", summary="Prometheus metrics endpoint", description="Exposes Prometheus metrics for the honeypot service.")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
