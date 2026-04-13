from features.synthetic_cognitive_memory.cognitive_memory import CognitiveMemory
from backend_api.analyzer.neural_threat_brain import brain as neural_threat_brain # Import the neural_threat_brain

class CognitiveCore:
    """
    Cognitive Core Intelligence: Blends symbolic logic and deep neural reasoning
    for context-aware threat analysis.
    """
    def __init__(self, cognitive_memory):
        self.known_threats = {
            "malware_signature_A": {"level": "critical", "description": "Known sophisticated malware variant."},
            "phishing_attempt_B": {"level": "high", "description": "Attempted phishing attack from a blacklisted IP."},
            "port_scan_C": {"level": "medium", "description": "Suspicious port scanning activity."},
            "unauthorized_access_D": {"level": "critical", "description": "Confirmed unauthorized access attempt."},
            "ddos_attack_E": {"level": "critical", "description": "Distributed Denial of Service attack in progress."}
        }
        self.memory = cognitive_memory
        print("Initializing Cognitive Core with shared Cognitive Memory...")

    def analyze_threat(self, threat_data):
        """
        Analyzes threat data using cognitive core intelligence and memory,
        integrating neural threat brain analysis.
        """
        print(f"Analyzing threat: {threat_data}")

        # Handle dictionary-based telemetry data
        if isinstance(threat_data, dict):
            if threat_data.get("cpu_usage", 0) > 90.0:
                analysis_result = {
                    "status": "analyzed",
                    "threat_level": "high",
                    "description": f"High CPU usage detected on node {threat_data.get('node_id')}.",
                    "threat_data_received": threat_data
                }
                self.memory.store_episode(str(threat_data), analysis_result, "Logged for performance review.")
                return analysis_result

        # Fallback to string-based analysis for other threat types
        threat_str = str(threat_data)
        recalled_episode = self.memory.recall_episode(threat_str)
        if recalled_episode:
            print("Threat recognized from cognitive memory.")
            return recalled_episode["analysis"]

        # Use NeuralThreatBrain for prediction and explanation
        neural_analysis = neural_threat_brain.predict(threat_str)
        
        threat_info = self.known_threats.get(threat_str)
        
        status = "analyzed"
        threat_level = neural_analysis["label"] # Use label from neural brain
        description = neural_analysis["explanation"] # Use explanation from neural brain

        # Override threat_level if a known threat is matched and is more critical
        if threat_info and self._is_more_critical(threat_info["level"], threat_level):
            threat_level = threat_info["level"]
            description = threat_info["description"]

        analysis_result = {
            "status": status,
            "threat_level": threat_level,
            "description": description,
            "threat_data_received": threat_str,
            "neural_analysis": neural_analysis # Include raw neural analysis for completeness
        }
        
        self.memory.store_episode(threat_str, analysis_result, "Logged for future analysis.")
        
        return analysis_result

    def _is_more_critical(self, level1, level2):
        """Helper to compare threat levels."""
        levels = {"low": 0, "medium": 1, "high": 2, "critical": 3, "NEGATIVE": 2, "POSITIVE": 0} # Map neural labels
        return levels.get(level1, -1) > levels.get(level2, -1)

    def execute_action(self, action: dict):
        """
        Executes a parsed action from the NSL parser.
        """
        print(f"Executing action: {action}")
        if action.get("intent") == "auto_isolation_trigger":
            print("--- ACTION: Auto-isolation protocol initiated.")
            print(f"--- REASON: Verification with {action.get('details')}")
            return {"status": "executed", "action": "auto_isolation"}
        else:
            print("--- ACTION: Unknown action.")
            return {"status": "failed", "reason": "Unknown action"}