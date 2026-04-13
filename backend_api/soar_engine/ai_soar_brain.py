import logging
from typing import Dict, Any, List, Optional, Tuple

from .models import Playbook

logger = logging.getLogger(__name__)

class AISoarBrain:
    """
    An AI-driven brain for the SOAR engine to make intelligent decisions.
    """

    def __init__(self, playbooks: List[Playbook]):
        self.playbooks = playbooks
        logger.info("AI SOAR Brain initialized.")

    def select_playbook(self, incident: Dict[str, Any]) -> Optional[Tuple[Playbook, float]]:
        """
        Selects the best playbook to execute for a given incident.

        Args:
            incident (Dict[str, Any]): The incident details.

        Returns:
            Optional[Tuple[Playbook, float]]: A tuple of the selected playbook and a confidence score, or None.
        """
        # A more advanced implementation would use a trained model to match incidents to playbooks.
        # For now, we'll use a heuristic-based approach.
        best_playbook = None
        highest_confidence = 0.0

        for playbook in self.playbooks:
            confidence = self._calculate_confidence(playbook, incident)
            if confidence > highest_confidence:
                highest_confidence = confidence
                best_playbook = playbook

        if best_playbook:
            return best_playbook, highest_confidence
        return None

    def _calculate_confidence(self, playbook: Playbook, incident: Dict[str, Any]) -> float:
        """
        Calculates a confidence score for a given playbook and incident.
        """
        # Simple heuristic:
        # - Base score of 0.5 if the trigger matches.
        # - Increase score based on severity match.
        # - Increase score based on keyword matches in the description.
        confidence = 0.0
        
        # Check trigger match
        trigger = playbook.trigger
        if trigger.get("event_type") == incident.get("event_type"):
            confidence += 0.5

            # Severity bonus
            if trigger.get("severity") == incident.get("severity"):
                confidence += 0.2

            # Keyword bonus
            description_keywords = playbook.description.lower().split()
            incident_keywords = incident.get("description", "").lower().split()
            matches = len(set(description_keywords) & set(incident_keywords))
            confidence += min(0.3, matches * 0.05)
            
        return min(1.0, confidence)

    def is_risk_aware(self, playbook: Playbook, context: Dict[str, Any]) -> bool:
        """
        Checks if it's safe to execute a playbook automatically.
        
        Args:
            playbook (Playbook): The playbook to check.
            context (Dict[str, Any]): The current context.

        Returns:
            bool: True if it's safe to execute, False otherwise.
        """
        # A more advanced implementation would use a risk score based on asset criticality, user roles, etc.
        # For now, we'll use a simple rule to avoid blocking critical assets.
        
        critical_assets = ["ceo_laptop", "dns_server"] # Example critical assets
        
        for step in playbook.steps:
            if step.action == "block_ip" or step.action == "isolate_host":
                # Check if the target is a critical asset
                target = step.parameters.get("host_id") or step.parameters.get("ip_address")
                if target in critical_assets:
                    logger.warning(f"High-risk action '{step.action}' on critical asset '{target}' detected. Manual approval required.")
                    return False
        
        return True
