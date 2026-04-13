from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import logging
import json
import os
import time
import uuid

from .simulation_modules import (
    run_xss_simulation,
    run_sqli_simulation,
    run_rce_simulation,
    run_privilege_escalation_simulation,
    run_ransomware_mimic_simulation,
    run_port_scan_simulation,
    run_bruteforce_simulation,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

SIMULATION_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "simulation_results")
os.makedirs(SIMULATION_RESULTS_DIR, exist_ok=True)


class SimulationRequest(BaseModel):
    simulation_type: str  # e.g., "xss", "sqli", "rce", "ransomware_mimic"
    target: str  # e.g., URL, IP address, hostname
    parameters: dict = {}


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "BAS Engine service is healthy"}


@app.post("/start_simulation")
async def start_simulation(
    request: SimulationRequest, background_tasks: BackgroundTasks
):
    simulation_id = str(uuid.uuid4())
    logger.info(
        f"Starting {request.simulation_type} simulation (ID: {simulation_id}) on target: {request.target}"
    )

    result_file = os.path.join(SIMULATION_RESULTS_DIR, f"{simulation_id}.json")

    # Map simulation type to function
    simulation_func = None
    if request.simulation_type == "xss":
        simulation_func = run_xss_simulation
    elif request.simulation_type == "sqli":
        simulation_func = run_sqli_simulation
    elif request.simulation_type == "rce":
        simulation_func = run_rce_simulation
    elif request.simulation_type == "privilege_escalation":
        simulation_func = run_privilege_escalation_simulation
    elif request.simulation_type == "ransomware_mimic":
        simulation_func = run_ransomware_mimic_simulation
    elif request.simulation_type == "port_scanning":
        simulation_func = run_port_scan_simulation
    elif request.simulation_type == "bruteforce":
        simulation_func = run_bruteforce_simulation
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown simulation type: {request.simulation_type}",
        )

    background_tasks.add_task(
        simulation_func, simulation_id, request.target, request.parameters, result_file
    )
    return {
        "message": "Simulation initiated in the background.",
        "simulation_id": simulation_id,
    }


@app.get("/simulation_results/{simulation_id}")
async def get_simulation_results(simulation_id: str):
    result_file = os.path.join(SIMULATION_RESULTS_DIR, f"{simulation_id}.json")
    if not os.path.exists(result_file):
        raise HTTPException(
            status_code=404,
            detail="Simulation results not found. May still be running.",
        )
    with open(result_file, "r") as f:
        results = json.load(f)
    return results


@app.get("/simulation_list")
async def get_simulation_list():
    simulations = []
    for filename in os.listdir(SIMULATION_RESULTS_DIR):
        if filename.endswith(".json"):
            simulation_id = filename.replace(".json", "")
            simulations.append(simulation_id)
    return {"simulations": simulations}
