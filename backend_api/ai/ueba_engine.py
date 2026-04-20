import json
import logging
from collections import defaultdict
from datetime import datetime
import numpy as np

logger = logging.getLogger("ueba_engine")

class UEBAEngine:
    """
    User & Entity Behavior Analytics Engine
    Calculates dynamic risk baselines for entities/users and flags anomalous behaviors.
    """
    def __init__(self):
        # In-memory baselines (in a real scenario, this would be backed by Redis/Cassandra)
        self.entity_baselines = defaultdict(lambda: {"event_count": 0, "failed_login_count": 0, "bytes_transferred": 0, "baseline_score": 0.0})
        self.entity_risk_scores = defaultdict(float)
        
        # Risk Multipliers
        self.risk_weights = {
            "authentication_failed": 15.0,
            "privilege_escalation_attempt": 35.0,
            "unusual_process_execution": 20.0,
            "data_exfiltration_attempt": 40.0,
            "multiple_failed_connections": 10.0,
            "lateral_movement_suspicion": 30.0
        }
        
        self.decay_factor = 0.95  # Score decays naturally over time

    def compute_decay(self):
        """Continuously decay risk scores over time if no new bad behavior occurs."""
        for entity in self.entity_risk_scores:
            if self.entity_risk_scores[entity] > 0.0:
                self.entity_risk_scores[entity] *= self.decay_factor

    def analyze_event(self, event: dict) -> dict:
        """
        Ingests an event, updates baselines, calculates immediate risk score, 
        and returns an anomaly object if the sequence is deemed suspicious.
        """
        entity_id = event.get('user_id') or event.get('agent_id') or 'unknown_entity'
        event_type = event.get('type')
        
        # Update baseline stats
        self.entity_baselines[entity_id]["event_count"] += 1
        
        anomaly = None
        risk_increase = self.risk_weights.get(event_type, 1.0)
        
        # Special behavioral logic checks
        if event_type == "authentication_failed":
            self.entity_baselines[entity_id]["failed_login_count"] += 1
            if self.entity_baselines[entity_id]["failed_login_count"] > 5:
                risk_increase += 25.0
                anomaly = self._generate_anomaly(entity_id, "Brute Force Authentication Attempt", event_type)
        
        elif event_type == "data_transfer":
            bytes_sent = event.get("data", {}).get("bytes_sent", 0)
            self.entity_baselines[entity_id]["bytes_transferred"] += bytes_sent
            # Very basic statistical outlier detection for data transfer (pseudo-logic)
            if bytes_sent > 500000000: # 500 MB
                risk_increase += self.risk_weights["data_exfiltration_attempt"]
                anomaly = self._generate_anomaly(entity_id, "Massive Data Transfer Detected", "data_exfiltration_attempt")

        elif event_type in ["privilege_escalation_attempt", "lateral_movement_suspicion"]:
            # Critical events instantly generate an anomaly
            anomaly = self._generate_anomaly(entity_id, f"Critical Event: {event_type}", event_type)
        
        # Apply Risk
        self.entity_risk_scores[entity_id] = min(100.0, self.entity_risk_scores[entity_id] + risk_increase)
        
        if self.entity_risk_scores[entity_id] >= 75.0 and not anomaly:
             anomaly = self._generate_anomaly(entity_id, "Entity Risk Score Exceeded Threshold", "high_entity_risk")
        
        if anomaly:
            anomaly["current_risk_score"] = self.entity_risk_scores[entity_id]
            anomaly["recommendation"] = self._get_recommendation(anomaly["type"], self.entity_risk_scores[entity_id])
            
        return anomaly

    def _generate_anomaly(self, entity_id: str, description: str, anomaly_type: str) -> dict:
        return {
            "entity_id": entity_id,
            "description": description,
            "type": anomaly_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def _get_recommendation(self, anomaly_type: str, score: float) -> str:
        if score > 90.0:
            return "IMMEDIATE ACTION REQUIRED: Isolate host and disable user account immediately via SOAR."
        
        recs = {
            "Brute Force Authentication Attempt": "Enforce MFA and temporarily lock the account. Verify origin IP.",
            "Massive Data Transfer Detected": "Investigate destination IP. Terminate network connection if unauthorized.",
            "Critical Event: privilege_escalation_attempt": "Isolate the agent. Hunt for compromised credentials.",
            "high_entity_risk": "Assign analyst to investigate entity timeline and recent processes."
        }
        return recs.get(anomaly_type, "Investigate entity behavior in the dashboard.")

