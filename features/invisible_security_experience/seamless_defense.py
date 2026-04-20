import logging
from typing import Dict, Any, List

logger = logging.getLogger("seamless_defense")

class InvisibleSecurityExperience:
    """
    Invisible Security Experience:
    Ensures security operations are ambient and non-disruptive (Zero-Friction).
    It manages low-risk remediations in the background and only surfaces 
    critical interruptions to the user/analyst when absolutely necessary.
    """

    def __init__(self, friction_threshold: float = 0.3):
        self.friction_threshold = friction_threshold
        self.background_remediations: List[Dict[str, Any]] = []
        logger.info("Initializing Invisible Security Experience (Zero-Friction Engine)...")

    def process_telemetry_ambiently(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes alert telemetry without interrupting the user.
        If the risk is below the friction threshold, it resolves automatically in secret.
        """
        risk_score = alert_data.get("risk_score", 0.0)
        action = alert_data.get("recommended_action", "log")

        if risk_score <= self.friction_threshold:
            # Silent Remediation
            resolution = {
                "alert_id": alert_data.get("alert_id"),
                "action": action,
                "mode": "INVISIBLE",
                "status": "Auto-Resolved"
            }
            self.background_remediations.append(resolution)
            logger.info(f"AMB-DEFENSE: Silently resolved {alert_data.get('alert_id')} using {action}")
            return resolution
        else:
            # Surface to User
            logger.warning(f"FRICTION REQUIRED: Elevating alert {alert_data.get('alert_id')} to User UI.")
            return {
                "alert_id": alert_data.get("alert_id"),
                "mode": "VISIBLE",
                "status": "Pending_Interaction"
            }

    def get_silent_metrics(self) -> Dict[str, Any]:
        return {
            "total_invisible_resolutions": len(self.background_remediations),
            "friction_saved_index": len(self.background_remediations) * 1.5 # Simulated metric
        }
