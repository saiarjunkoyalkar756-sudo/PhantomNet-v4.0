import numpy as np
from phantomnet_agent.p2p_communication import P2PNode
from shared.platform_utils import get_os, OS_TERMUX
import logging
from shared.ml_adapter import MLAdapter # Import MLAdapter

logger = logging.getLogger(__name__)

class CognitiveCore:
    def __init__(self):
        self.current_os = get_os()
        self.safe_ai_mode = self.current_os == OS_TERMUX # Enable safe mode for Termux
        logger.info(f"CognitiveCore initialized for OS: {self.current_os}. Safe AI Mode: {self.safe_ai_mode}")

        self.symbolic_rules = {
            "potential_ddos": lambda data: data.get("request_frequency", 0) > 100,
            "suspicious_payload": lambda data: "malware" in data.get("payload", ""),
        }
        self.ml_adapter = MLAdapter(model_path="path/to/your/model.keras") # Initialize MLAdapter
        logger.info(f"MLAdapter initialized in mode: {self.ml_adapter.current_ml_mode}")

        self.ethical_layer = EthicalAI()
        self.p2p_node = P2PNode("0.0.0.0", 9999, self)
        self.p2p_node.start()

    def analyze_threat(self, data):
        # Symbolic analysis
        symbolic_alerts = [
            rule for rule, checker in self.symbolic_rules.items() if checker(data)
        ]

        # Neural analysis using MLAdapter
        # For a real implementation, 'data' would be preprocessed into features for the ML model.
        # Here, we use a dummy input for the MLAdapter.
        ml_input = np.array([[data.get("request_frequency", 0), data.get("payload_size", 0)]]) # Example features
        ml_prediction_result = self.ml_adapter.predict(ml_input)
        neural_prediction = ml_prediction_result["prediction"][0][0] # Assuming single scalar output
        logger.debug(f"Neural prediction ({ml_prediction_result['mode']}): {neural_prediction}")

        # Combine analyses
        is_threat = len(symbolic_alerts) > 0 or neural_prediction > 0.6

        # Ethical oversight
        if not self.ethical_layer.is_action_fair(data, is_threat):
            return {"threat": False, "reason": "Ethical override: Action deemed unfair"}

        if is_threat:
            self.broadcast_alert(data)

        return {
            "threat": is_threat,
            "symbolic_alerts": symbolic_alerts,
            "neural_prediction": float(neural_prediction),
        }

    def broadcast_alert(self, alert_data):
        message = {"type": "alert", "data": alert_data}
        self.p2p_node.broadcast(message)

    def handle_peer_alert(self, alert_data):
        print(f"[Cognitive Core] Received alert from peer: {alert_data}")
        # Future enhancement: Update internal models or trigger defensive actions based on peer alerts


class EthicalAI:
    def is_action_fair(self, data, is_threat):
        # Placeholder for fairness and bias checks
        if is_threat and data.get("source_ip") == "127.0.0.1":
            return False  # Avoid blocking localhost
        return True
