import logging
from typing import Dict, Any, List, Optional
import math

logger = logging.getLogger("fusion_engine")

class FusionEngine:
    """
    Cross-Domain Fusion Intelligence:
    Integrates diverse data streams (Psychological, Economic, Linguistic, and Technical) 
    to predict and detect complex human-driven attacks and insider threats.
    
    Uses a Weighted Multi-Vector Fusion logic to calculate a 'Threat Probability Index'.
    """

    def __init__(self):
        # State tracking for users/entities
        self.entity_intelligence: Dict[str, Dict[str, Any]] = {}
        logger.info("Initializing Cross-Domain Fusion Intelligence Engine...")

    def _get_or_create_entity(self, entity_id: str) -> Dict[str, Any]:
        if entity_id not in self.entity_intelligence:
            self.entity_intelligence[entity_id] = {
                "psych_score": 0.0,
                "econ_score": 0.0,
                "ling_score": 0.0,
                "tech_score": 0.0,
                "events": []
            }
        return self.entity_intelligence[entity_id]

    def ingest_telemetry(self, entity_id: str, domain: str, metadata: Dict[str, Any]):
        """
        Ingests data from a specific domain and updates the entity's risk profile.
        Domains: 'psychological', 'economic', 'linguistic', 'technical'
        """
        entity = self._get_or_create_entity(entity_id)
        
        # Mapping domain to specific risk calculations
        if domain == "psychological":
            # Stress, fatigue, dissatisfaction markers
            entity["psych_score"] = float(metadata.get("stress_index", 0.0))
        elif domain == "economic":
            # Unusual expenditures, debt, market fluctuations
            entity["econ_score"] = float(metadata.get("financial_pressure_index", 0.0))
        elif domain == "linguistic":
            # Tone shift, urgent phrasing, deceptive markers
            entity["ling_score"] = float(metadata.get("deception_probability", 0.0))
        elif domain == "technical":
            # Unaligned port access, shadow IT detected
            entity["tech_score"] = float(metadata.get("anomaly_score", 0.0))

        entity["events"].append({"domain": domain, "data": metadata})
        logger.info(f"Fusion Telemetry Updated for {entity_id} in {domain} domain.")

    def calculate_attack_probability(self, entity_id: str) -> Dict[str, Any]:
        """
        Fuses multi-domain intelligence using a weighted geometric mean.
        The fusion reflects that high risk in multiple disparate domains 
        is significantly more dangerous than high risk in just one.
        """
        if entity_id not in self.entity_intelligence:
            return {"status": "error", "message": "Unknown entity."}
            
        e = self.entity_intelligence[entity_id]
        
        # Weights: Technical and Linguistic carry more weight in current PhantomNet v4
        weights = {"psych": 0.15, "econ": 0.20, "ling": 0.35, "tech": 0.30}
        
        # Base scores (0.0 to 1.0)
        fusion_score = (
            (e["psych_score"] * weights["psych"]) +
            (e["econ_score"] * weights["econ"]) +
            (e["ling_score"] * weights["ling"]) +
            (e["tech_score"] * weights["tech"])
        )
        
        # Synergy Factor: If multiple domains are above 0.7, boost the risk exponentially
        high_risk_count = sum(1 for s in [e["psych_score"], e["econ_score"], e["ling_score"], e["tech_score"]] if s > 0.7)
        if high_risk_count >= 2:
            fusion_score = min(1.0, fusion_score * (1.2 ** high_risk_count))

        risk_level = "LOW"
        if fusion_score > 0.85: risk_level = "CRITICAL"
        elif fusion_score > 0.65: risk_level = "HIGH"
        elif fusion_score > 0.40: risk_level = "MEDIUM"

        return {
            "entity_id": entity_id,
            "fusion_risk_score": float(fusion_score),
            "risk_level": risk_level,
            "high_risk_count": high_risk_count,
            "analysis_domains": ["psychological", "economic", "linguistic", "technical"],
            "prediction": self._generate_prediction_text(risk_level, high_risk_count)
        }

    def _generate_prediction_text(self, risk_level: str, high_risk_count: int) -> str:
        if risk_level == "CRITICAL":
            return "Extreme risk of coordinated insider threat or sophisticated social engineering. Immediate intervention required."
        if risk_level == "HIGH":
            return "Significant multi-vector risk detected. High confidence in impending malicious activity."
        if high_risk_count > 0:
            return "Localized anomalous behavior detected. Monitor cross-domain correlations."
        return "Stable behavior signature. No imminent threat detected."

    def predict_human_driven_attack(self, user_id: str):
        """Compatibility wrapper for legacy calls."""
        return self.calculate_attack_probability(user_id)
