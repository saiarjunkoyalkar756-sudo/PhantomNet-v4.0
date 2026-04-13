import asyncio
from typing import Dict, Any

class RiskIndexPredictor:
    """
    Predicts a comprehensive risk index for a given threat event based on
    various factors and historical data.
    """
    def __init__(self):
        print("RiskIndexPredictor initialized.")

    async def predict_risk(self, threat_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a risk score and identifies contributing risk factors.
        """
        await asyncio.sleep(0.01) # Simulate async operation
        risk_score = 0.5
        risk_factors = ["Initial assessment based on event type."]

        # Example: Increase risk for critical severity events
        if threat_event.get("severity") == "critical":
            risk_score += 0.3
            risk_factors.append("Critical severity event detected.")
        
        # Example: Adjust based on context confidence
        if threat_event.get("context_confidence", 0) < 0.5:
            risk_score += 0.1
            risk_factors.append("Low confidence in threat context.")

        risk_score = min(1.0, max(0.0, risk_score)) # Clamp between 0 and 1

        return {
            "risk_score": risk_score * 100, # Convert to 0-100 scale
            "risk_factors": risk_factors
        }
