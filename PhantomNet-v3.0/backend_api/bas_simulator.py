# backend_api/bas_simulator.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import random
import time
import uuid
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Data Models for BAS Operations ---
class AttackScenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the simulation scenario")
    name: str = Field(..., description="Name of the attack scenario (e.g., 'Phishing Campaign', 'SQL Injection')")
    description: str = Field(..., description="Description of the simulated attack.")
    attack_type: str = Field(..., description="Type of attack (e.g., 'phishing', 'ransomware', 'sqli')")
    target_asset: str = Field(..., description="Target asset or user for the simulation")
    attack_vector: str = Field(..., description="Method of attack delivery (e.g., 'email', 'web_app', 'network')")
    risk_level: str = Field(..., description="Simulated risk level ('low', 'medium', 'high', 'critical')")

class SimulationResult(BaseModel):
    simulation_id: str = Field(..., description="Unique ID for the simulation run")
    scenario_id: str = Field(..., description="ID of the executed attack scenario")
    status: str = Field("running", description="Status of the simulation ('running', 'detected', 'prevented', 'successful', 'failed')")
    start_time: float = Field(default_factory=time.time, description="Timestamp when simulation started")
    end_time: Optional[float] = Field(None, description="Timestamp when simulation ended")
    detection_points: List[Dict[str, Any]] = Field([], description="Details on where/when the attack was detected")
    impact_assessment: Dict[str, Any] = Field({}, description="Simulated impact if the attack was successful")
    remediation_suggestions: List[str] = Field([], description="Suggested remediations based on simulation outcome")
    score: float = Field(0.0, ge=0, le=100, description="Effectiveness score of current defenses (0-100)")
    raw_logs: List[str] = Field([], description="Simulated raw logs generated during the attack")

class BASSimulator:
    def __init__(self):
        self.active_simulations: Dict[str, SimulationResult] = {}

    async def _simulate_phishing(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates a phishing attack scenario."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(30, 90) # Random defense score
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(5, 10)) # Simulate duration

        if result.score > 70: # High defense score
            result.status = "prevented"
            result.detection_points.append({"stage": "email_gateway", "action": "blocked_email", "timestamp": time.time()})
            result.remediation_suggestions.append("Maintain strong email filtering rules.")
        elif result.score > 40: # Medium defense score
            result.status = "detected"
            result.detection_points.append({"stage": "user_report", "action": "user_reported_phishing", "timestamp": time.time()})
            result.impact_assessment = {"data_exposure": "low", "user_compromise": "isolated"}
            result.remediation_suggestions.append("Improve user security awareness training.")
        else: # Low defense score
            result.status = "successful"
            result.impact_assessment = {"data_exposure": "high", "user_compromise": "widespread", "financial_loss": "potential"}
            result.remediation_suggestions.append("Implement multi-factor authentication and endpoint detection & response (EDR).")
        
        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Email to {scenario.target_asset} flagged by gateway.",
            f"[{time.time()}] WARN: User clicked on suspicious link in phishing simulation.",
            f"[{time.time()}] ALERT: Phishing attack successful, credentials harvested." if result.status == "successful" else ""
        ]
        return result

    async def _simulate_ransomware(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates a ransomware attack scenario."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(20, 80)
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(8, 15))

        if result.score > 60:
            result.status = "prevented"
            result.detection_points.append({"stage": "endpoint_protection", "action": "blocked_execution", "timestamp": time.time()})
            result.remediation_suggestions.append("Keep endpoint security up-to-date and conduct regular vulnerability scans.")
        elif result.score > 30:
            result.status = "detected"
            result.detection_points.append({"stage": "file_integrity_monitoring", "action": "detected_unauthorized_encryption", "timestamp": time.time()})
            result.impact_assessment = {"data_encryption": "partial", "system_downtime": "moderate"}
            result.remediation_suggestions.append("Implement robust backup and recovery strategies, and network segmentation.")
        else:
            result.status = "successful"
            result.impact_assessment = {"data_encryption": "widespread", "system_downtime": "severe", "financial_loss": "significant"}
            result.remediation_suggestions.append("Deploy behavior-based ransomware detection and isolation mechanisms.")
        
        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Ransomware payload executed on {scenario.target_asset}.",
            f"[{time.time()}] ALERT: Multiple files encrypted on target system.",
            f"[{time.time()}] ERROR: Ransom note found, system locked." if result.status == "successful" else ""
        ]
        return result
    
    async def _simulate_sqli(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates an SQL Injection attack."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(40, 95)
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(3, 7))

        if result.score > 80:
            result.status = "prevented"
            result.detection_points.append({"stage": "waf", "action": "blocked_injection_attempt", "timestamp": time.time()})
            result.remediation_suggestions.append("Ensure WAF rules are updated and input validation is enforced.")
        elif result.score > 50:
            result.status = "detected"
            result.detection_points.append({"stage": "ids", "action": "detected_anomalous_db_query", "timestamp": time.time()})
            result.impact_assessment = {"data_access": "limited", "data_exfiltration": "attempted"}
            result.remediation_suggestions.append("Implement parameterized queries and least privilege access to databases.")
        else:
            result.status = "successful"
            result.impact_assessment = {"data_access": "full", "data_exfiltration": "confirmed", "system_manipulation": "possible"}
            result.remediation_suggestions.append("Conduct regular code reviews for SQLi vulnerabilities and deploy database activity monitoring (DAM).")
        
        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Web application received suspicious SQL query.",
            f"[{time.time()}] ALERT: SQL Injection detected, database credentials exposed." if result.status == "successful" else ""
        ]
        return result


    async def run_simulation(self, scenario: AttackScenario) -> SimulationResult:
        """
        Runs a simulated attack based on the provided scenario.
        """
        if scenario.attack_type == "phishing":
            result = await self._simulate_phishing(scenario)
        elif scenario.attack_type == "ransomware":
            result = await self._simulate_ransomware(scenario)
        elif scenario.attack_type == "sqli":
            result = await self._simulate_sqli(scenario)
        # Add more attack types here
        else:
            raise ValueError(f"Unknown attack type: {scenario.attack_type}")
        
        self.active_simulations[result.simulation_id] = result # Update with final result
        logger.info(f"[{__name__}] Simulation '{scenario.name}' ({result.simulation_id}) finished with status: {result.status}")
        return result

    def get_simulation_result(self, simulation_id: str) -> Optional[SimulationResult]:
        """Retrieves the result of a specific simulation."""
        return self.active_simulations.get(simulation_id)
    
    def get_all_simulations(self) -> List[SimulationResult]:
        """Retrieves all performed simulation results."""
        return list(self.active_simulations.values())

if __name__ == "__main__":
    simulator = BASSimulator()

    async def test_bas_simulator():
        print("--- Testing Phishing Simulation ---")
        phishing_scenario = AttackScenario(
            name="Executive Phishing",
            description="Simulated email phishing targeting executive credentials.",
            attack_type="phishing",
            target_asset="ceo@example.com",
            attack_vector="email",
            risk_level="high"
        )
        phishing_result = await simulator.run_simulation(phishing_scenario)
        print(json.dumps(phishing_result.dict(), indent=2))

        print("\n--- Testing Ransomware Simulation ---")
        ransomware_scenario = AttackScenario(
            name="SMB Ransomware",
            description="Simulated ransomware spreading via SMB exploit.",
            attack_type="ransomware",
            target_asset="file_server_01",
            attack_vector="network",
            risk_level="critical"
        )
        ransomware_result = await simulator.run_simulation(ransomware_scenario)
        print(json.dumps(ransomware_result.dict(), indent=2))

        print(f"\n--- Retrieving Simulation {phishing_result.simulation_id} ---")
        retrieved_phishing = simulator.get_simulation_result(phishing_result.simulation_id)
        print(json.dumps(retrieved_phishing.dict(), indent=2)) if retrieved_phishing else "Simulation not found."

        print("\n--- Retrieving All Simulations ---")
        all_sims = simulator.get_all_simulations()
        print(json.dumps([s.dict() for s in all_sims], indent=2))

    asyncio.run(test_bas_simulator())
