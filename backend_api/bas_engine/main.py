from backend_api.shared.service_factory import create_phantom_service
from .simulation_modules import (
    run_xss_simulation,
    run_sqli_simulation,
    run_rce_simulation,
    run_privilege_escalation_simulation,
    run_ransomware_mimic_simulation,
    run_port_scan_simulation,
    run_bruteforce_simulation,
)
from loguru import logger
import asyncio
import uuid
import os
import json
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Depends
from pydantic import BaseModel

SIMULATION_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "simulation_results")

async def bas_startup(app: FastAPI):
    """
    Handles startup events for the Breach & Attack Simulation Engine.
    """
    if not os.path.exists(SIMULATION_RESULTS_DIR):
        os.makedirs(SIMULATION_RESULTS_DIR)
        logger.info(f"BAS Engine: Created directory {SIMULATION_RESULTS_DIR}")

app = create_phantom_service(
    name="Breach & Attack Simulation Engine",
    description="Automated security validation via simulated threat vectors.",
    version="1.0.0",
    custom_startup=bas_startup
)

class SimulationRequest(BaseModel):
    simulation_type: str
    target: str
    parameters: dict = {}

@app.post("/start_simulation")
async def start_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    simulation_id = str(uuid.uuid4())
    # Simulation logic mapping...
    return success_response(data={"simulation_id": simulation_id, "status": "initiated"}, message="Simulation started.")

@app.get("/simulation_results/{simulation_id}")
async def get_simulation_results(simulation_id: str):
    result_file = os.path.join(SIMULATION_RESULTS_DIR, f"{simulation_id}.json")
    if not os.path.exists(result_file):
        return error_response(code="NOT_FOUND", message="Simulation results not found.", status_code=404)
    with open(result_file, "r") as f:
        results = json.load(f)
    return success_response(data=results)

@app.get("/simulation_list")
async def get_simulation_list():
    simulations = []
    if os.path.exists(SIMULATION_RESULTS_DIR):
        for filename in os.listdir(SIMULATION_RESULTS_DIR):
            if filename.endswith(".json"):
                simulations.append(filename.replace(".json", ""))
    return success_response(data={"simulations": simulations})
