import logging
from typing import Dict, Any, List

logger = logging.getLogger("autonomy_manager")

class AutonomyManager:
    """
    AI Autonomy Levels (A1–A5):
    Defines the operational constraints and authorization levels for PhantomNet AI.
    
    A1: HUMAN_ASSISTED - Read-only telemetry, all actions require manual trigger.
    A2: HUMAN_CONFIRMED - AI proposes actions, human must click 'Approve'.
    A3: HUMAN_SUPERVISED - AI auto-executes, but alerts human for immediate rollback option.
    A4: CONSTRAINED_AUTONOMY - AI auto-executes on non-critical assets (score < 7).
    A5: FULL_AUTONOMY - AI has full override authority across the entire ecosystem.
    """

    LEVELS = ["A1", "A2", "A3", "A4", "A5"]

    def __init__(self, default_level: str = "A2"):
        self.current_autonomy_level = default_level if default_level in self.LEVELS else "A1"
        self.audit_history: List[Dict[str, Any]] = []
        logger.info(f"AI Autonomy Manager initialized at Level: {self.current_autonomy_level}")

    def set_autonomy_level(self, level: str, authorizer: str = "SYSTEM_ROOT") -> Dict[str, Any]:
        """
        Transitions the system to a new autonomy level. Requires authorization logs.
        """
        if level not in self.LEVELS:
            logger.error(f"Invalid Autonomy Level requested: {level}")
            return {"status": "error", "message": f"Level {level} not recognized."}

        old_level = self.current_autonomy_level
        self.current_autonomy_level = level
        
        log_entry = {
            "timestamp": uuid.uuid4().hex, # placeholder for timestamp
            "old_level": old_level,
            "new_level": level,
            "authorizer": authorizer
        }
        self.audit_history.append(log_entry)
        
        logger.warning(f"AUTONOMY TRANSITION: {old_level} -> {level} by {authorizer}")
        return {"status": "success", "level": self.current_autonomy_level}

    def can_auto_execute(self, asset_criticality: int = 5) -> bool:
        """
        Returns True if the current autonomy level permits autonomous action 
        without human intervention for a given asset.
        """
        level = self.current_autonomy_level
        
        if level == "A5":
            return True
        if level == "A4" and asset_criticality < 7:
            return True
        if level == "A3":
            # A3 auto-executes then notifies, so we return True here
            return True
        
        return False

import uuid
