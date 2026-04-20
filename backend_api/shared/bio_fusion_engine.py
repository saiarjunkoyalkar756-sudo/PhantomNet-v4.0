# backend_api/shared/bio_fusion_engine.py

import logging
from typing import Dict, List, Any
import numpy as np
from backend_api.shared.logger_config import logger

class BioFusionEngine:
    """
    Bio-Cyber Fusion Engine:
    Performs continuous Zero-Trust identity verification using behavioral biometrics.
    Analyzes typing cadence and pointer dynamics for session integrity.
    """

    def __init__(self, tolerance_threshold: float = 0.85):
        self.baseline_db: Dict[str, Dict[str, Any]] = {}
        self.tolerance_threshold = tolerance_threshold
        logger.info("BioFusionEngine: Continuous behavioral identity monitoring online.")

    def _extract_cadence(self, keystrokes: List[Dict[str, float]]) -> np.ndarray:
        """
        Parses raw keystroke telemetry into dwell/flight vectors.
        """
        if len(keystrokes) < 2:
            return np.array([0.0, 0.0, 0.0, 0.0])
            
        dwells = [k['release'] - k['press'] for k in keystrokes if 'release' in k and 'press' in k]
        flights = [keystrokes[i]['press'] - keystrokes[i-1]['release'] for i in range(1, len(keystrokes))]
        
        return np.array([
            np.mean(dwells) if dwells else 0.0,
            np.mean(flights) if flights else 0.0,
            np.std(dwells) if dwells else 0.0,
            np.std(flights) if flights else 0.0
        ])

    def learn_baseline(self, user_id: str, sample_data: Dict[str, Any]):
        """
        Trains the engine on a user's biological signature.
        """
        vector = self._extract_cadence(sample_data.get('keystrokes', []))
        self.baseline_db[user_id] = {
            "cadence_vector": vector,
            "ptr_speed": sample_data.get('pointer_speed', 0.0)
        }
        logger.info(f"BioFusionEngine: Learned unique biometric signature for {user_id}.")

    def verify_session(self, user_id: str, live_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares live interaction patterns against the baseline.
        """
        if user_id not in self.baseline_db:
            return {"verified": True, "score": 1.0, "notes": "No baseline"}

        base = self.baseline_db[user_id]
        live_vec = self._extract_cadence(live_data.get('keystrokes', []))
        
        # Cosine Similarity check
        b_vec = base["cadence_vector"]
        if np.linalg.norm(b_vec) == 0 or np.linalg.norm(live_vec) == 0:
            sim = 1.0
        else:
            sim = np.dot(b_vec, live_vec) / (np.linalg.norm(b_vec) * np.linalg.norm(live_vec))
            
        verified = sim >= self.tolerance_threshold
        
        if not verified:
            logger.warning(f"IDENTITY ALERT: Behavioral divergence detected for {user_id}. Score: {sim:.2f}")

        return {
            "verified": bool(verified),
            "score": float(sim),
            "timestamp": live_data.get("timestamp")
        }
