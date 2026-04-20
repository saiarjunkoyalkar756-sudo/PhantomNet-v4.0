import logging
import math
from typing import Dict, List, Any
import numpy as np

logger = logging.getLogger("behavioral_biometrics")

class BioCyberFusion:
    """
    Bio-Cyber Fusion (Digital Immunology & Behavioral Biometrics)
    Provides Continuous Zero-Trust Authentication by analyzing human-machine interaction patterns.
    
    If an attacker steals a primary token but their typing cadence (keystroke dynamics) 
    or pointer dynamics do not match the biological owner, the agent cuts the session.
    """

    def __init__(self, tolerance_threshold: float = 0.85):
        logger.info("Initializing Bio-Cyber Digital Immunology Engine...")
        self.baseline_db: Dict[str, Dict[str, Any]] = {}
        self.tolerance_threshold = tolerance_threshold

    def _extract_typing_cadence(self, keystroke_events: List[Dict[str, float]]) -> np.ndarray:
        """
        Calculates dwell time (key press duration) and flight time (time between keys).
        """
        if len(keystroke_events) < 2:
            return np.array([0.0])
            
        dwell_times = []
        flight_times = []
        
        # Keystroke events format: [{'key': 'a', 'press': 1.1, 'release': 1.25}, ...]
        for i in range(len(keystroke_events)):
            current = keystroke_events[i]
            # Calculate Dwell
            if 'press' in current and 'release' in current:
                dwell_times.append(current['release'] - current['press'])
            
            # Calculate Flight
            if i > 0:
                prev = keystroke_events[i-1]
                if 'release' in prev and 'press' in current:
                    flight_times.append(current['press'] - prev['release'])
                    
        dwell_avg = np.mean(dwell_times) if dwell_times else 0.0
        flight_avg = np.mean(flight_times) if flight_times else 0.0
        return np.array([dwell_avg, flight_avg, np.std(dwell_times), np.std(flight_times)])

    def register_biological_baseline(self, entity_id: str, biometric_data: Dict[str, Any]):
        """
        Trains the initial baseline for the user's biological signature.
        """
        keystrokes = biometric_data.get('keystroke_events', [])
        pointer_speed_avg = biometric_data.get('pointer_speed_avg', 0.0)
        
        vector = self._extract_typing_cadence(keystrokes)
        
        self.baseline_db[entity_id] = {
            "cadence_vector": vector,
            "pointer_speed_avg": pointer_speed_avg
        }
        logger.info(f"Bio-signature learned and registered for entity: {entity_id}")
        return True

    def analyze_biometric_session(self, entity_id: str, live_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Continuously models live biological telemetry against the stored digital immune baseline.
        If it diverges beyond the tolerance threshold, it flags foreign presence.
        """
        if entity_id not in self.baseline_db:
            return {"status": "error", "message": f"No biological baseline found for {entity_id}"}
            
        baseline = self.baseline_db[entity_id]
        live_vector = self._extract_typing_cadence(live_data.get('keystroke_events', []))
        live_pointer = live_data.get('pointer_speed_avg', baseline['pointer_speed_avg'])

        # Calculate Cosine Similarity for the typing cadence vector
        b_vec = baseline["cadence_vector"]
        if np.linalg.norm(b_vec) == 0 or np.linalg.norm(live_vector) == 0:
            cadence_similarity = 1.0 # Not enough data
        else:
            cadence_similarity = np.dot(b_vec, live_vector) / (np.linalg.norm(b_vec) * np.linalg.norm(live_vector))
            
        # Analyze behavioral pointer dynamics
        pointer_deviation = abs(baseline['pointer_speed_avg'] - live_pointer) / max(baseline['pointer_speed_avg'], 1)
        pointer_similarity = max(0.0, 1.0 - pointer_deviation)
        
        # Blended biometric score
        fusion_score = (cadence_similarity * 0.70) + (pointer_similarity * 0.30)
        
        identity_verified = fusion_score >= self.tolerance_threshold
        
        result = {
            "status": "analyzed",
            "entity_id": entity_id,
            "fusion_score": float(fusion_score),
            "identity_verified": bool(identity_verified)
        }
        
        if not identity_verified:
            logger.warning(f"BIO-CYBER FUSION ALERT: Foreign biological interaction detected on session {entity_id}. Score: {fusion_score:.2f}")
            result["alerts"] = ["Biological cadence mismatch. Possible session hijacking."]
            
        return result
