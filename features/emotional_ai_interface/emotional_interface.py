import logging
from typing import Dict, Any, List

logger = logging.getLogger("emotional_ai")

class EmotionalAIInterface:
    """
    Emotional AI Interface:
    Analyzes the 'emotional telemetry' of the human-in-the-loop (SOC Analyst).
    Detects signs of fatigue, stress, or anxiety through interaction patterns 
    and adjusts the system's output to minimize cognitive load during critical incidents.
    """

    def __init__(self):
        logger.info("Initializing Emotional AI Interface (Cognitive Load Optimizer)...")
        self.analyst_state: Dict[str, Any] = {
            "fatigue_index": 0.0,
            "stress_level": 0.0,
            "interaction_velocity": 1.0 # Normal
        }

    def analyze_analyst_telemetry(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes typing speed, mouse jitter, and response latency to gauge emotional state.
        """
        latency = interaction_data.get("command_latency", 1.0)
        mouse_jitter = interaction_data.get("mouse_jitter", 0.0)
        
        # Heuristic calculation
        if latency > 5.0 and mouse_jitter > 0.5:
            self.analyst_state["fatigue_index"] = 0.8
            self.analyst_state["stress_level"] = 0.9
        elif latency < 1.0:
            self.analyst_state["fatigue_index"] = 0.1
            self.analyst_state["stress_level"] = 0.2
            
        logger.info(f"Analyst Emotion State: Friction={self.analyst_state['fatigue_index']}, Stress={self.analyst_state['stress_level']}")
        return self.analyst_state

    def adjust_ui_for_emotion(self) -> Dict[str, str]:
        """
        Returns UI adjustment recommendations based on the analyst's emotional state.
        """
        if self.analyst_state["stress_level"] > 0.7:
            return {
                "ui_mode": "ZEN_MODE",
                "color_palette": "SOFT_BLUE",
                "notification_level": "MINIMAL",
                "suggestion": "Critical Alerts only. Suppressing background noise to lower stress."
            }
        return {
            "ui_mode": "STANDARD",
            "color_palette": "CYBER_NEON",
            "notification_level": "FULL",
            "suggestion": "Full telemetry stream active."
        }
