# backend_api/soar_engine/playbook_flow_builder.py

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from shared.logger_config import logger
from .models import Playbook, PlaybookStep, RemediationAction # Import Playbook and PlaybookStep

logger = logger

class AIPlaybookGenerator:
    """
    Generates playbook steps or entire playbooks based on incident context using AI.
    Also supports validation and conversion for a visual builder.
    """
    def __init__(self):
        logger.info("AIPlaybookGenerator initialized.")
        # In a real scenario, this would interface with an LLM or a rule-based AI engine
        # self.llm_client = LLMClient()
        # self.rule_engine = RuleEngine()

    async def generate_playbook_from_incident(self, incident: Dict[str, Any]) -> Playbook:
        """
        Generates a new playbook dynamically based on the incident details.
        This is a conceptual AI generation.
        """
        logger.info(f"AI generating playbook for incident: {incident.get('incident_id')}")
        
        # Simulate AI analysis and step generation
        if incident.get("event_type") == "malicious_ip_detected":
            generated_steps = [
                PlaybookStep(
                    action=RemediationAction.ENRICH_INDICATOR,
                    tool_name="ThreatIntel",
                    parameters={"value": incident.get("source_ip"), "type": "ip"},
                    output_to="enriched_ip",
                    description="Enrich source IP using Threat Intelligence."
                ),
                PlaybookStep(
                    action=RemediationAction.BLOCK_IP,
                    tool_name="Firewall",
                    parameters={"ip_address": "{context.enriched_ip.indicator.value}"},
                    condition="context.enriched_ip.reputation_score > 70",
                    description="Block IP if TI score is high."
                ),
                PlaybookStep(
                    action=RemediationAction.CREATE_TICKET,
                    tool_name="TicketingSystem",
                    parameters={"title": f"High Severity IP Blocked: {incident.get('source_ip')}", "description": "AI-generated ticket for blocked malicious IP."},
                    description="Create a ticket for tracking."
                )
            ]
        elif incident.get("event_type") == "suspicious_login":
            generated_steps = [
                PlaybookStep(
                    action=RemediationAction.NOTIFY_USER,
                    tool_name="Messaging",
                    parameters={"user_id": incident.get("user_id"), "message": "Suspicious login detected on your account."},
                    description="Notify affected user."
                ),
                PlaybookStep(
                    action=RemediationAction.RESET_PASSWORD,
                    tool_name="IAM",
                    parameters={"user_id": incident.get("user_id")},
                    requires_approval=True,
                    description="Request approval to reset user password."
                )
            ]
        else:
            generated_steps = [
                PlaybookStep(
                    action=RemediationAction.CREATE_TICKET,
                    tool_name="TicketingSystem",
                    parameters={"title": f"Incident: {incident.get('event_type')}", "description": f"AI-generated ticket for incident {incident.get('incident_id')}."}
                )
            ]

        generated_playbook = Playbook(
            name=f"AI_Generated_PB_{incident.get('event_type')}_{incident.get('incident_id')}",
            description=f"Auto-generated playbook for incident: {incident.get('incident_id')}",
            trigger={"incident_id": incident.get('incident_id')}, # Link to specific incident
            steps=generated_steps,
            context={"incident": incident}
        )
        return generated_playbook

    def validate_playbook(self, playbook: Playbook) -> List[str]:
        """
        Validates a playbook's structure and step parameters.
        Returns a list of error messages, or empty list if valid.
        """
        errors = []
        if not playbook.name:
            errors.append("Playbook name cannot be empty.")
        if not playbook.steps:
            errors.append("Playbook must have at least one step.")
        
        for i, step in enumerate(playbook.steps):
            if not step.action:
                errors.append(f"Step {i}: Action cannot be empty.")
            # Further validation based on tool_name and expected parameters
        return errors

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running AIPlaybookGenerator example...")
    
    mock_incident = {
        "incident_id": "INC-003",
        "event_type": "malicious_ip_detected",
        "source_ip": "4.4.4.4",
        "host_id": "endpoint-456",
        "severity": "high",
        "user_id": "alice"
    }

    async def run_example():
        generator = AIPlaybookGenerator()
        generated_playbook = await generator.generate_playbook_from_incident(mock_incident)
        logger.info(f"Generated Playbook:\n{generated_playbook.model_dump_json(indent=2)}")
        
        errors = generator.validate_playbook(generated_playbook)
        if errors:
            logger.error(f"Validation errors: {errors}")
        else:
            logger.info("Generated playbook is valid.")

    try:
        import asyncio
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("AIPlaybookGenerator example stopped.")
