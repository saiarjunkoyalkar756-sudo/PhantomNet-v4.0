# backend_api/soar_engine/pse.py
import logging
from typing import Dict, Any, List, Tuple, Optional

# Assuming models are defined in a shared location
# from .models import Playbook
# For now, using a dictionary to represent a playbook
Playbook = Dict[str, Any]

logger = logging.getLogger(__name__)


class PlaybookStrategyEngine:
    """
    Selects the optimal playbook based on the incoming alert context using a scoring mechanism.
    """

    def __init__(self, playbooks: List[Playbook]):
        self.playbooks = {pb["name"]: pb for pb in playbooks}
        logger.info(
            f"Playbook Strategy Engine (PSE) initialized with {len(self.playbooks)} playbooks."
        )

    def _score_playbook(self, playbook: Playbook, alert_context: Dict[str, Any]) -> float:
        """
        Calculates a confidence score for how well a playbook matches an alert.
        The score is between 0.0 and 1.0.
        """
        score = 0.0
        
        # Factor 1: Trigger Matching (40% weight)
        # This is the primary filter. If the trigger doesn't match, the score is 0.
        trigger = playbook.get("trigger", {})
        alert_trigger_info = alert_context.get("trigger_info", {})
        
        trigger_type_match = trigger.get("type") == alert_trigger_info.get("type")
        trigger_subtype_match = trigger.get("subtype") == alert_trigger_info.get("subtype")

        if not trigger_type_match:
            return 0.0
        
        if trigger_subtype_match:
            score += 0.40 # Perfect trigger match
        else:
            score += 0.20 # Partial match on type only

        # Factor 2: AI Confidence (30% weight)
        ai_confidence = alert_context.get("ai_confidence", 0.0)
        score += ai_confidence * 0.30

        # Factor 3: Asset Criticality Alignment (20% weight)
        # Does the playbook's intended criticality match the asset's?
        asset_criticality = alert_context.get("asset_criticality", 1)
        playbook_criticality_level = playbook.get("metadata", {}).get("intended_criticality", 5)
        
        # Simple scoring: closer the criticality, higher the score
        criticality_diff = abs(asset_criticality - playbook_criticality_level) / 10.0
        score += (1.0 - criticality_diff) * 0.20
        
        # Factor 4: Historical Success Rate (10% weight)
        # This would be fed by the Reinforcement Learning Module in the full architecture.
        historical_success = playbook.get("metadata", {}).get("historical_success_rate", 0.7) # Default 70%
        score += historical_success * 0.10

        return min(1.0, score)

    def select_playbook(
        self, alert_context: Dict[str, Any]
    ) -> Optional[Tuple[Playbook, float]]:
        """
        Iterates through all available playbooks and returns the one with the highest score.

        Args:
            alert_context (Dict[str, Any]): The enriched alert from the AI engine, including
                                             AI confidence, asset info, and trigger details.

        Returns:
            Optional[Tuple[Playbook, float]]: A tuple of the best playbook and its score,
                                              or None if no suitable playbook is found.
        """
        best_playbook: Optional[Playbook] = None
        highest_score = 0.0

        for playbook in self.playbooks.values():
            score = self._score_playbook(playbook, alert_context)
            if score > highest_score:
                highest_score = score
                best_playbook = playbook

        if best_playbook:
            logger.info(
                f"Selected playbook '{best_playbook['name']}' with a confidence score of {highest_score:.2f}"
            )
            return best_playbook, highest_score

        logger.warning(
            f"No suitable playbook found for the given alert context: {alert_context}"
        )
        return None

# Example Usage
def main():
    # Mock playbooks, similar to what would be loaded from a database or files
    mock_playbooks = [
        {
            "name": "critical_host_compromise_remediation",
            "trigger": {"type": "security", "subtype": "host_compromise"},
            "metadata": {"intended_criticality": 9, "historical_success_rate": 0.85},
            "steps": ["..."],
        },
        {
            "name": "generic_malware_containment",
            "trigger": {"type": "security", "subtype": "malware_detection"},
            "metadata": {"intended_criticality": 5, "historical_success_rate": 0.90},
            "steps": ["..."],
        },
        {
            "name": "suspicious_network_traffic_analysis",
            "trigger": {"type": "security", "subtype": "suspicious_network"},
            "metadata": {"intended_criticality": 3, "historical_success_rate": 0.95},
            "steps": ["..."],
        },
    ]

    pse = PlaybookStrategyEngine(mock_playbooks)

    # --- Test Case 1: High-confidence alert on a critical asset ---
    alert1 = {
        "ai_confidence": 0.95,
        "asset_criticality": 10,
        "trigger_info": {"type": "security", "subtype": "host_compromise"},
    }
    print("--- Use Case 1: Critical Host Compromise ---")
    selection1 = pse.select_playbook(alert1)
    if selection1:
        playbook, score = selection1
        print(f"Selected Playbook: {playbook['name']} (Score: {score:.2f})") # Expected: critical_host_compromise_remediation
    
    print("\n")

    # --- Test Case 2: Lower-confidence alert, generic malware ---
    alert2 = {
        "ai_confidence": 0.70,
        "asset_criticality": 4,
        "trigger_info": {"type": "security", "subtype": "malware_detection"},
    }
    print("--- Use Case 2: Generic Malware Alert ---")
    selection2 = pse.select_playbook(alert2)
    if selection2:
        playbook, score = selection2
        print(f"Selected Playbook: {playbook['name']} (Score: {score:.2f})") # Expected: generic_malware_containment

if __name__ == "__main__":
    main()
