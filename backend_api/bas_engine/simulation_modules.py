# backend_api/bas_engine/simulation_modules.py
import os
import json
import asyncio
from loguru import logger
from backend_api.shared.bas_simulator import BASSimulator, AttackScenario

SIMULATION_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "simulation_results")

def save_result(simulation_id: str, result_dict: dict):
    if not os.path.exists(SIMULATION_RESULTS_DIR):
        os.makedirs(SIMULATION_RESULTS_DIR, exist_ok=True)
    result_file = os.path.join(SIMULATION_RESULTS_DIR, f"{simulation_id}.json")
    with open(result_file, "w") as f:
        json.dump(result_dict, f, indent=4)

async def execute_simulator_scenario(scenario_name: str, attack_type: str, target: str, params: dict, simulation_id: str):
    try:
        simulator = BASSimulator()
        scenario = AttackScenario(
            scenario_id=simulation_id,
            name=scenario_name,
            description=f"Simulated {scenario_name} attack targeting {target}.",
            attack_type=attack_type,
            target_asset=target,
            attack_vector="web_app" if attack_type in ["sqli", "xss", "rce"] else "network",
            risk_level="high"
        )
        # run_simulation is an async method
        result = await simulator.run_simulation(scenario)
        result_dict = result.model_dump()
        save_result(simulation_id, result_dict)
        logger.info(f"BAS Engine: Simulation {simulation_id} completed successfully.")
    except Exception as e:
        logger.error(f"BAS Engine: Failed to execute simulation {simulation_id}: {e}")
        save_result(simulation_id, {
            "simulation_id": simulation_id,
            "status": "failed",
            "error": str(e)
        })

def run_xss_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("Cross-Site Scripting (XSS)", "xss", target, params, simulation_id))

def run_sqli_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("SQL Injection (SQLi)", "sqli", target, params, simulation_id))

def run_rce_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("Remote Code Execution (RCE)", "rce", target, params, simulation_id))

def run_privilege_escalation_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("Privilege Escalation", "privilege_escalation", target, params, simulation_id))

def run_ransomware_mimic_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("Ransomware Mimic", "ransomware", target, params, simulation_id))

def run_port_scan_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("Port Scan", "port_scan", target, params, simulation_id))

def run_bruteforce_simulation(target: str, params: dict, simulation_id: str):
    asyncio.create_task(execute_simulator_scenario("Credential Bruteforce", "bruteforce", target, params, simulation_id))
