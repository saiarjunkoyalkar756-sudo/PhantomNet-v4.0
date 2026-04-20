import logging
from typing import Dict, Any, List

logger = logging.getLogger("incident_assistant")

class EmotionallyAwareIncidentAssistant:
    """
    Emotionally Aware Incident Assistant:
    A specialized AI partner that adapts its communication style and 
    automated assistance based on the severity of the incident 
    and the detected emotional state of the human analyst.
    """

    def __init__(self):
        logger.info("Initializing Emotionally Aware Incident Assistant (EAIA)...")

    def provide_assistance(self, incident_data: Dict[str, Any], emotional_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates assistance logic and adjusted messaging.
        """
        severity = incident_data.get("severity", "medium").lower()
        is_stressed = emotional_state.get("stress_level", 0.0) > 0.6
        
        # Tone Logic
        if is_stressed:
            tone = "Calm, Direct, and Brief"
            msg = "I have prioritized the top 3 actions for you. Focus on Host Isolation first."
        elif severity == "critical":
            tone = "Urgent, Descriptive, and Supportive"
            msg = "CRITICAL BREACH: I am standing by to auto-remediate. Please authorize the isolation of Sector 7."
        else:
            tone = "Informative and Conversational"
            msg = "Incident detected. I've gathered the initial logs for your review whenever you're ready."

        response = {
            "assistant_tone": tone,
            "personalized_message": msg,
            "automated_actions_ready": ["Block IP", "Snapshot Config"] if severity == "critical" else ["Log Analysis"],
            "support_mode": "ACTIVE" if is_stressed else "STANDBY"
        }
        
        logger.info(f"EAIA Assistant Mode: Tone={tone}")
        return response

    def get_assistant_version(self):
        return "1.0.0-PROTOTYPE"
