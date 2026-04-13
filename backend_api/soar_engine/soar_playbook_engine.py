# backend_api/soar_engine/soar_playbook_engine.py
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# from .models import Playbook, PlaybookRun, PlaybookStatus  # Using dicts for now
# from .auto_response_engine import AutoResponseEngine
# from .human_in_the_loop import HumanInTheLoop
from .pse import PlaybookStrategyEngine
from .sbra import SimulationBlastRadiusAnalyzer

Playbook = Dict[str, Any]
PlaybookRun = Dict[str, Any]

logger = logging.getLogger(__name__)

# Confidence and Impact Thresholds for Autonomous Action
CONFIDENCE_THRESHOLD = 0.75  # Minimum playbook score to be considered
AUTONOMOUS_EXECUTION_THRESHOLD = 0.90  # Score above which full auto is allowed
MAX_IMPACT_FOR_AUTONOMY = 4  # Max business impact (1-10) for autonomous action


from backend_api.shared.audit_log import AUDIT_LOG_QUEUE

class SOARPlaybookEngine:
    """
    An autonomous decision engine that selects, simulates, and executes
    playbooks based on risk and confidence.
    """

    def __init__(self, playbooks: List[Playbook]):
        self.playbook_strategy_engine = PlaybookStrategyEngine(playbooks)
        self.blast_radius_analyzer = SimulationBlastRadiusAnalyzer()
        self.running_playbooks: Dict[str, asyncio.Task] = {}
        logger.info("Autonomous SOAR Decision Engine initialized.")

    async def _execute_playbook(self, playbook: Playbook, alert: Dict[str, Any]):
        """
        (Conceptual) Executes a playbook and logs the action for notarization.
        """
        logger.info(
            f"Executing playbook '{playbook['name']}' for alert '{alert['alert_id']}'..."
        )
        await asyncio.sleep(1)  # Simulate execution time
        
        # Create an audit record of the autonomous action
        audit_record = {
            "service": "soar_engine",
            "action": "execute_playbook",
            "playbook_name": playbook['name'],
            "alert_id": alert['alert_id'],
            "decision": "AUTONOMOUS_EXECUTION",
            "timestamp": datetime.utcnow().isoformat(),
        }
        await AUDIT_LOG_QUEUE.put(audit_record)
        logger.info(f"Playbook execution record sent for notarization.")

        logger.info(f"Playbook '{playbook['name']}' executed successfully.")
        return {"status": "completed", "steps_run": len(playbook["steps"])}

    async def _escalate_for_approval(
        self, playbook: Playbook, alert: Dict[str, Any], reason: str
    ):
        """
        (Conceptual) Escalates a decision and logs the escalation for notarization.
        """
        logger.warning(
            f"Escalating playbook '{playbook['name']}' for alert '{alert['alert_id']}'. Reason: {reason}"
        )
        
        # Create an audit record of the escalation
        audit_record = {
            "service": "soar_engine",
            "action": "escalate_for_approval",
            "playbook_name": playbook['name'],
            "alert_id": alert['alert_id'],
            "decision": "HUMAN_IN_THE_LOOP_REQUIRED",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await AUDIT_LOG_QUEUE.put(audit_record)
        logger.info(f"Escalation record sent for notarization.")

        await asyncio.sleep(0.1)
        return {"status": "escalated", "reason": reason}

    def _get_primary_disruptive_action(
        self, playbook: Playbook
    ) -> Optional[str]:
        """
        Finds the first highly disruptive action in a playbook to simulate.
        """
        disruptive_actions = ["isolate_host", "shutdown_service", "block_ip"]
        for step in playbook.get("steps", []):
            if step.get("action") in disruptive_actions:
                return step["action"]
        return None

    async def process_alert(self, alert: Dict[str, Any]):
        """
        Processes an incoming alert through the full autonomous decision workflow.
        """
        logger.info(f"\n--- Processing new alert: {alert['alert_id']} ---")

        # 1. Select Best Playbook
        selection = self.playbook_strategy_engine.select_playbook(alert)
        if not selection or selection[1] < CONFIDENCE_THRESHOLD:
            logger.warning(
                f"No suitable playbook found or score too low. Alert '{alert['alert_id']}' requires manual review."
            )
            return

        playbook, playbook_score = selection
        logger.info(
            f"Step 1: Playbook Selected. Name: '{playbook['name']}', Score: {playbook_score:.2f}"
        )

        # 2. Simulate & Analyze Blast Radius
        target_asset = alert.get("asset_id")
        primary_action = self._get_primary_disruptive_action(playbook)
        business_impact = 1  # Default to low impact

        if target_asset and primary_action:
            impact, _ = await self.blast_radius_analyzer.calculate_impact(
                target_asset, primary_action
            )
            business_impact = impact
            logger.info(
                f"Step 2: Simulation Complete. Business Impact Score: {business_impact}/10"
            )
        else:
            logger.info(
                "Step 2: Simulation Skipped. No disruptive action or target asset found."
            )

        # 3. Make Autonomous Decision
        logger.info("Step 3: Making Autonomous Decision...")
        ai_confidence = alert.get("ai_confidence", 0.0)

        # Logic for autonomous execution
        if (
            playbook_score >= AUTONOMOUS_EXECUTION_THRESHOLD
            and business_impact <= MAX_IMPACT_FOR_AUTONOMY
        ):
            logger.info(
                f"Decision: Execute Autonomously. (Playbook Score {playbook_score:.2f} >= {AUTONOMOUS_EXECUTION_THRESHOLD} AND Impact {business_impact} <= {MAX_IMPACT_FOR_AUTONOMY})"
            )
            await self._execute_playbook(playbook, alert)
        # Logic for escalation
        else:
            reason = ""
            if playbook_score < AUTONOMOUS_EXECUTION_THRESHOLD:
                reason += f"Playbook score ({playbook_score:.2f}) is below the autonomy threshold ({AUTONOMOUS_EXECUTION_THRESHOLD}). "
            if business_impact > MAX_IMPACT_FOR_AUTONOMY:
                reason += f"Business impact ({business_impact}) is above the autonomy threshold ({MAX_IMPACT_FOR_AUTONOMY}). "
            logger.info(f"Decision: Escalate for Human Approval. Reason: {reason}")
            await self._escalate_for_approval(playbook, alert, reason)


# Example Usage
async def main():
    logger.info("Initializing Autonomous Decision Engine Example...")

    # Mock Playbooks
    mock_playbooks = [
        {
            "name": "critical_host_compromise_remediation",
            "trigger": {"type": "security", "subtype": "host_compromise"},
            "metadata": {"intended_criticality": 9},
            "steps": [{"action": "isolate_host"}, {"action": "create_ticket"}],
        },
        {
            "name": "generic_malware_containment",
            "trigger": {"type": "security", "subtype": "malware_detection"},
            "metadata": {"intended_criticality": 5},
            "steps": [{"action": "block_hash"}, {"action": "run_scanner"}],
        },
    ]

    engine = SOARPlaybookEngine(mock_playbooks)

    # --- Use Case 1: Clear and present danger, low impact ---
    # High AI confidence on a non-critical asset, perfect playbook match.
    alert1 = {
        "alert_id": "ALERT-001",
        "ai_confidence": 0.98,
        "asset_id": "frontend-web",  # Assumed to have low-to-mid impact
        "asset_criticality": 7,
        "trigger_info": {"type": "security", "subtype": "host_compromise"},
    }
    await engine.process_alert(alert1)
    # EXPECTED: Autonomous Execution

    # --- Use Case 2: Clear and present danger, HIGH impact ---
    # High AI confidence but on a critical database.
    alert2 = {
        "alert_id": "ALERT-002",
        "ai_confidence": 0.98,
        "asset_id": "prod-db-01",  # This is a critical asset with many dependents
        "asset_criticality": 10,
        "trigger_info": {"type": "security", "subtype": "host_compromise"},
    }
    await engine.process_alert(alert2)
    # EXPECTED: Escalation for Human Approval due to high business impact

    # --- Use Case 3: Ambiguous threat ---
    # Lower AI confidence, playbook score will not meet autonomy threshold.
    alert3 = {
        "alert_id": "ALERT-003",
        "ai_confidence": 0.70,  # Below AUTONOMOUS_EXECUTION_THRESHOLD
        "asset_id": "frontend-web",
        "asset_criticality": 7,
        "trigger_info": {"type": "security", "subtype": "host_compromise"},
    }
    await engine.process_alert(alert3)
    # EXPECTED: Escalation for Human Approval due to low confidence


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    # To run this example, the asset_inventory_service must be running on port 8008
    # E.g., uvicorn backend_api.asset_inventory_service.main:app --port 8008
    # In a separate terminal.
    asyncio.run(main())
