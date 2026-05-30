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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from backend_api.shared.file_logging import get_rotating_file_logger
attack_sim_file_logger = get_rotating_file_logger("attack_simulation", "attack_simulation.log")


# --- Data Models for BAS Operations ---
class AttackScenario(BaseModel):
    scenario_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for the simulation scenario",
    )
    name: str = Field(
        ...,
        description="Name of the attack scenario (e.g., 'Phishing Campaign', 'SQL Injection')",
    )
    description: str = Field(..., description="Description of the simulated attack.")
    attack_type: str = Field(
        ..., description="Type of attack (e.g., 'phishing', 'ransomware', 'sqli')"
    )
    target_asset: str = Field(
        ..., description="Target asset or user for the simulation"
    )
    attack_vector: str = Field(
        ...,
        description="Method of attack delivery (e.g., 'email', 'web_app', 'network')",
    )
    risk_level: str = Field(
        ..., description="Simulated risk level ('low', 'medium', 'high', 'critical')"
    )


class SimulationResult(BaseModel):
    simulation_id: str = Field(..., description="Unique ID for the simulation run")
    scenario_id: str = Field(..., description="ID of the executed attack scenario")
    status: str = Field(
        "running",
        description="Status of the simulation ('running', 'detected', 'prevented', 'successful', 'failed')",
    )
    start_time: float = Field(
        default_factory=time.time, description="Timestamp when simulation started"
    )
    end_time: Optional[float] = Field(
        None, description="Timestamp when simulation ended"
    )
    detection_points: List[Dict[str, Any]] = Field(
        [], description="Details on where/when the attack was detected"
    )
    impact_assessment: Dict[str, Any] = Field(
        {}, description="Simulated impact if the attack was successful"
    )
    remediation_suggestions: List[str] = Field(
        [], description="Suggested remediations based on simulation outcome"
    )
    score: float = Field(
        0.0, ge=0, le=100, description="Effectiveness score of current defenses (0-100)"
    )
    raw_logs: List[str] = Field(
        [], description="Simulated raw logs generated during the attack"
    )


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
            score=random.uniform(30, 90),  # Random defense score
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(5, 10))  # Simulate duration

        if result.score > 70:  # High defense score
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "email_gateway",
                    "action": "blocked_email",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Maintain strong email filtering rules."
            )
        elif result.score > 40:  # Medium defense score
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "user_report",
                    "action": "user_reported_phishing",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "data_exposure": "low",
                "user_compromise": "isolated",
            }
            result.remediation_suggestions.append(
                "Improve user security awareness training."
            )
        else:  # Low defense score
            result.status = "successful"
            result.impact_assessment = {
                "data_exposure": "high",
                "user_compromise": "widespread",
                "financial_loss": "potential",
            }
            result.remediation_suggestions.append(
                "Implement multi-factor authentication and endpoint detection & response (EDR)."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Email to {scenario.target_asset} flagged by gateway.",
            f"[{time.time()}] WARN: User clicked on suspicious link in phishing simulation.",
            (
                f"[{time.time()}] ALERT: Phishing attack successful, credentials harvested."
                if result.status == "successful"
                else ""
            ),
        ]
        return result

    async def _simulate_ransomware(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates a ransomware attack scenario."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(20, 80),
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(8, 15))

        if result.score > 60:
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "endpoint_protection",
                    "action": "blocked_execution",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Keep endpoint security up-to-date and conduct regular vulnerability scans."
            )
        elif result.score > 30:
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "file_integrity_monitoring",
                    "action": "detected_unauthorized_encryption",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "data_encryption": "partial",
                "system_downtime": "moderate",
            }
            result.remediation_suggestions.append(
                "Implement robust backup and recovery strategies, and network segmentation."
            )
        else:
            result.status = "successful"
            result.impact_assessment = {
                "data_encryption": "widespread",
                "system_downtime": "severe",
                "financial_loss": "significant",
            }
            result.remediation_suggestions.append(
                "Deploy behavior-based ransomware detection and isolation mechanisms."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Ransomware payload executed on {scenario.target_asset}.",
            f"[{time.time()}] ALERT: Multiple files encrypted on target system.",
            (
                f"[{time.time()}] ERROR: Ransom note found, system locked."
                if result.status == "successful"
                else ""
            ),
        ]
        return result

    async def _simulate_sqli(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates an SQL Injection attack."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(40, 95),
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(3, 7))

        if result.score > 80:
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "waf",
                    "action": "blocked_injection_attempt",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Ensure WAF rules are updated and input validation is enforced."
            )
        elif result.score > 50:
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "ids",
                    "action": "detected_anomalous_db_query",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "data_access": "limited",
                "data_exfiltration": "attempted",
            }
            result.remediation_suggestions.append(
                "Implement parameterized queries and least privilege access to databases."
            )
        else:
            result.status = "successful"
            result.impact_assessment = {
                "data_access": "full",
                "data_exfiltration": "confirmed",
                "system_manipulation": "possible",
            }
            result.remediation_suggestions.append(
                "Conduct regular code reviews for SQLi vulnerabilities and deploy database activity monitoring (DAM)."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Web application received suspicious SQL query.",
            (
                f"[{time.time()}] ALERT: SQL Injection detected, database credentials exposed."
                if result.status == "successful"
                else ""
            ),
        ]
        return result

    async def _simulate_lateral_movement(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates an advanced Lateral Movement campaign (e.g., PSExec, SSH, Pass-the-Hash)."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(40, 95),
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(3, 6))

        if result.score > 75:
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "network_segmentation",
                    "action": "blocked_ssh_port_forwarding",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Implement strict microsegmentation, restrict local admin SSH privileges, and configure bastion hosts."
            )
        elif result.score > 45:
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "lateral_movement_detector",
                    "action": "alerted_anomalous_psexec_execution",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "movement_scope": "limited_workstations",
                "privilege_scope": "standard_user",
            }
            result.remediation_suggestions.append(
                "Deploy Remote Credential Guard, alert security analysts on local admin authentications, and restrict admin tools."
            )
        else:
            result.status = "successful"
            result.impact_assessment = {
                "movement_scope": "domain_wide",
                "privilege_scope": "domain_admin",
                "compromised_controllers": ["primary_domain_controller"],
            }
            result.remediation_suggestions.append(
                "Limit workstation-to-workstation communication, rotate Kerberos tickets (krbtgt), and audit credential vaults."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Host-to-host movement attempt detected from external pivot point targeting {scenario.target_asset}.",
            (
                f"[{time.time()}] ALERT: Lateral Movement detected via Remote Services (T1021) / Service Execution (T1569.002)."
                if result.status != "prevented"
                else f"[{time.time()}] INFO: Lateral movement blocked by port filtration/firewall."
            ),
        ]
        return result

    async def _simulate_credential_access(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates advanced Credential Access campaigns (e.g., Mimikatz LSASS memory dumping)."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(35, 90),
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(4, 7))

        if result.score > 70:
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "lsass_protection",
                    "action": "blocked_memory_dump_attempt",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Keep LSA Protection (RunAsPPL) enabled, and activate credential guard."
            )
        elif result.score > 40:
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "edr_agent",
                    "action": "detected_lsass_process_access",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "credentials_exposed": "partial_hashes",
                "remediation_status": "alerted",
            }
            result.remediation_suggestions.append(
                "Configure SOC alerts for anomalous process handles requesting access to lsass.exe."
            )
        else:
            result.status = "successful"
            result.impact_assessment = {
                "credentials_exposed": "cleartext_domain_admin",
                "hash_harvest": "widespread",
            }
            result.remediation_suggestions.append(
                "Enforce multi-factor authentication across all administration paths, restrict SeDebugPrivilege, and rotate high-privilege keys."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Process access handle requested for lsass.exe by unauthorized binary.",
            (
                f"[{time.time()}] ALERT: LSASS memory dump attempt detected (T1003 OS Credential Dumping)."
                if result.status != "prevented"
                else f"[{time.time()}] INFO: LSASS protection rule blocked read access to lsass memory space."
            ),
        ]
        return result

    async def _simulate_privilege_escalation(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates advanced Privilege Escalation campaigns (e.g., token impersonation, kernel exploit, UAC bypass)."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(30, 95),
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(3, 5))

        if result.score > 75:
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "application_control",
                    "action": "blocked_uac_bypass_execution",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Enforce patched operating system baselines and restrict administrative elevation rules via AppLocker/WDAC."
            )
        elif result.score > 40:
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "agent_behavioral_engine",
                    "action": "detected_token_impersonation",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "elevation_scope": "local_admin_only",
                "persistence_status": "none",
            }
            result.remediation_suggestions.append(
                "Monitor and block command interpreter elevation from non-administrative parent processes."
            )
        else:
            result.status = "successful"
            result.impact_assessment = {
                "elevation_scope": "system_root",
                "integrity_level": "system",
                "persistence_status": "compromised",
            }
            result.remediation_suggestions.append(
                "Audit high-privileged local accounts, patch system kernels immediately, and enforce least privilege roles."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Attempt to spawn elevated subprocess from unprivileged shell.",
            (
                f"[{time.time()}] ALERT: Privilege Escalation detected (T1068 Exploitation for Privilege Escalation / T1548 Abuse of Elevation Control)."
                if result.status != "prevented"
                else f"[{time.time()}] INFO: Integrity elevation blocked by operating system access control policies."
            ),
        ]
        return result

    async def _simulate_exfiltration(self, scenario: AttackScenario) -> SimulationResult:
        """Simulates advanced Data Exfiltration campaigns (e.g., DNS Tunneling, HTTPS large uploads)."""
        simulation_id = str(uuid.uuid4())
        result = SimulationResult(
            simulation_id=simulation_id,
            scenario_id=scenario.scenario_id,
            status="running",
            score=random.uniform(40, 95),
        )
        self.active_simulations[simulation_id] = result
        await asyncio.sleep(random.uniform(4, 6))

        if result.score > 80:
            result.status = "prevented"
            result.detection_points.append(
                {
                    "stage": "dlp_gateway",
                    "action": "blocked_encrypted_tunnel_connection",
                    "timestamp": time.time(),
                }
            )
            result.remediation_suggestions.append(
                "Deploy SSL/TLS inspection, enforce strict data egress control policies, and block unauthorized cloud upload destinations."
            )
        elif result.score > 50:
            result.status = "detected"
            result.detection_points.append(
                {
                    "stage": "dns_firewall",
                    "action": "detected_anomalous_dns_query_volume",
                    "timestamp": time.time(),
                }
            )
            result.impact_assessment = {
                "exfiltration_volume_mb": 150,
                "data_sensitivity": "pii_medium",
            }
            result.remediation_suggestions.append(
                "Configure anomalies checks for outbound DNS query payload sizes, and enforce standard external proxy usage."
            )
        else:
            result.status = "successful"
            result.impact_assessment = {
                "exfiltration_volume_mb": 42000,
                "data_sensitivity": "intellectual_property_high",
                "customer_records_exposed": 25000,
            }
            result.remediation_suggestions.append(
                "Deploy comprehensive Data Loss Prevention (DLP) solutions and classify sensitive databases to trigger direct egress stops."
            )

        result.end_time = time.time()
        result.raw_logs = [
            f"[{time.time()}] INFO: Anomalous volume outbound network transfer initiated to unclassified external IP address.",
            (
                f"[{time.time()}] ALERT: Potential Data Exfiltration detected (T1048 Exfiltration Over Alternative Protocol)."
                if result.status != "prevented"
                else f"[{time.time()}] INFO: Outbound network transfer payload size limit triggered. Connection severed."
            ),
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
        elif scenario.attack_type == "lateral_movement":
            result = await self._simulate_lateral_movement(scenario)
        elif scenario.attack_type == "credential_access":
            result = await self._simulate_credential_access(scenario)
        elif scenario.attack_type == "privilege_escalation":
            result = await self._simulate_privilege_escalation(scenario)
        elif scenario.attack_type == "exfiltration":
            result = await self._simulate_exfiltration(scenario)
        else:
            raise ValueError(f"Unknown attack type: {scenario.attack_type}")

        self.active_simulations[result.simulation_id] = (
            result  # Update with final result
        )
        logger.info(
            f"[{__name__}] Simulation '{scenario.name}' ({result.simulation_id}) finished with status: {result.status}"
        )
        try:
            attack_type = scenario.attack_type
            status = result.status
            blocked = (status == "prevented")
            score = result.score
            
            if attack_type == "sqli":
                payload = "UNION SELECT username, password FROM users"
            elif attack_type == "phishing":
                payload = "Subject: Urgent account verification required"
            elif attack_type == "ransomware":
                payload = "vssadmin.exe delete shadows /all /quiet"
            elif attack_type == "lateral_movement":
                payload = "psexec.exe \\\\domain-controller cmd.exe"
            elif attack_type == "credential_access":
                payload = "mimikatz.exe sekurlsa::logonpasswords"
            elif attack_type == "privilege_escalation":
                payload = "bypassuac.exe"
            elif attack_type == "exfiltration":
                payload = "DNS tunnel upload client.zip"
            else:
                payload = "None"
                
            source_ip = "10.0.0.10"
            if hasattr(scenario, "target_asset") and scenario.target_asset:
                if scenario.target_asset.startswith("ceo@"):
                    source_ip = "192.168.1.55"
                elif "workstation" in scenario.target_asset:
                    source_ip = "192.168.1.104"
                elif "server" in scenario.target_asset or "db" in scenario.target_asset or "controller" in scenario.target_asset:
                    source_ip = "10.0.0.22"
            
            attack_sim_file_logger.info(
                f"Attack simulation executed - Name: {scenario.name}, Type: {attack_type}, Target: {scenario.target_asset}, "
                f"Source IP: {source_ip}, Payload Snippet: '{payload}', Threat/Defense Score: {score:.2f}, Status: {status}, Blocked: {blocked}"
            )
        except Exception as log_err:
            logger.error(f"Error writing to attack_simulation.log: {log_err}")
            
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
            risk_level="high",
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
            risk_level="critical",
        )
        ransomware_result = await simulator.run_simulation(ransomware_scenario)
        print(json.dumps(ransomware_result.dict(), indent=2))

        print(f"\n--- Retrieving Simulation {phishing_result.simulation_id} ---")
        retrieved_phishing = simulator.get_simulation_result(
            phishing_result.simulation_id
        )
        (
            print(json.dumps(retrieved_phishing.dict(), indent=2))
            if retrieved_phishing
            else "Simulation not found."
        )

        print("\n--- Retrieving All Simulations ---")
        all_sims = simulator.get_all_simulations()
        print(json.dumps([s.dict() for s in all_sims], indent=2))

    asyncio.run(test_bas_simulator())
