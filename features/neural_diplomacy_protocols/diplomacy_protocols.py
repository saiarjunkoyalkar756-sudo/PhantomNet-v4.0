import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger("diplomacy_protocols")

class NeuralDiplomacyProtocols:
    """
    Neural Diplomacy Protocols:
    Enables PhantomNet AIs to negotiate response actions with other internal departments 
    or external security ecosystems (e.g., Cloud Providers, ISPs, other PhantomNet instances).
    
    Handles conflict resolution (e.g., Security wants ISOLATE, Operations wants UPTIME).
    """

    def __init__(self, reputation_threshold: float = 0.5):
        self.reputation_threshold = reputation_threshold
        # Tracks trust in external AIs/departments
        self.peer_reputations = {
            "department_ops": 0.9,
            "department_security": 1.0,
            "external_aws_waf": 0.8
        }
        logger.info("Initializing Neural Diplomacy Protocols with Reputation-Based weighting.")

    def negotiate_response(self, threat_data: Dict[str, Any], requester_id: str, proposed_action: str) -> Dict[str, Any]:
        """
        Negotiates a joint threat response, balancing security risk vs business impact.
        """
        logger.info(f"Negotiating {proposed_action} from {requester_id} for threat index {threat_data.get('alert_id')}")

        requester_trust = self.peer_reputations.get(requester_id, 0.5)
        
        # Policy conflict simulation
        # Security wants isolation, Ops might want to maintain service
        business_impact = threat_data.get("business_impact", 5) # 1-10
        threat_criticality = threat_data.get("threat_level", "medium")
        
        # Criticality Weight: low=1, med=2, high=5, critical=10
        crit_map = {"low": 1, "medium": 3, "high": 7, "critical": 10}
        threat_weight = crit_map.get(threat_criticality.lower(), 1)

        # Negotiation Score: (Threat Weight * Requester Trust) - (Business Impact)
        negotiation_score = (threat_weight * requester_trust) - (business_impact * 0.5)
        
        if negotiation_score > 5.0:
            decision = "APPROVED"
            reason = "Threat weight and requester trust outweigh business impact."
        elif negotiation_score > 2.0:
            decision = "PARTIAL_REMEDIATION"
            reason = "Balanced risk: Rate-limiting action approved instead of full isolation."
            proposed_action = "RATE_LIMIT"
        else:
            decision = "REJECTED"
            reason = "High business impact with insufficient threat weight for this autonomous action."

        result = {
            "status": "negotiated",
            "decision": decision,
            "resolved_action": proposed_action,
            "negotiation_score": float(negotiation_score),
            "reason": reason,
            "requester_id": requester_id
        }
        
        logger.info(f"Diplomacy Result for {requester_id}: {decision} ({reason})")
        return result

    def update_peer_reputation(self, peer_id: str, success: bool):
        """Adjusts trust based on the success/accuracy of past proposed actions."""
        current = self.peer_reputations.get(peer_id, 0.5)
        delta = 0.05 if success else -0.1
        self.peer_reputations[peer_id] = max(0.0, min(1.0, current + delta))
