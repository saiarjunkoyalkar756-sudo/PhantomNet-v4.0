# plugins/agent_personality_blue_team/blue_team_personality_entry.py
import json
import random
import time

def analyze_threat(threat_data: dict) -> dict:
    """
    Simulates a Blue Team AI agent analyzing a threat.
    """
    print(f"[{__name__}] Blue Team AI analyzing threat: {threat_data.get('type', 'N/A')}")
    time.sleep(random.uniform(0.5, 1.5)) # Simulate analysis time

    threat_type = threat_data.get("type", "unknown")
    severity = threat_data.get("severity", "medium")
    source_ip = threat_data.get("source_ip", "N/A")

    recommendations = []
    if severity == "critical" or "malware" in threat_type:
        recommendations.append("Isolate affected host.")
        recommendations.append("Block source IP at perimeter firewall.")
        recommendations.append("Initiate forensic analysis.")
    elif severity == "high" or "exploit" in threat_type:
        recommendations.append("Verify patch status of target systems.")
        recommendations.append("Monitor network traffic from source IP closely.")
    elif severity == "medium" or "scan" in threat_type:
        recommendations.append("Log and monitor activity.")
    else:
        recommendations.append("Continue monitoring.")

    response_phrases = [
        f"Threat '{threat_type}' from {source_ip} detected. Prioritizing defense.",
        f"Assessing '{threat_type}' severity as {severity}. Formulating response.",
        f"Engaging defensive protocols for detected '{threat_type}' activity.",
        f"Blue Team analysis complete. Recommendations generated."
    ]

    analysis_result = {
        "summary": random.choice(response_phrases),
        "threat_type": threat_type,
        "severity": severity,
        "source_ip": source_ip,
        "recommendations": recommendations,
        "confidence": round(random.uniform(0.7, 0.99), 2)
    }
    print(f"[{__name__}] Blue Team AI analysis completed for threat: {threat_type}")
    return analysis_result

def recommend_action(current_situation: dict) -> dict:
    """
    Simulates a Blue Team AI agent recommending an action based on the current situation.
    """
    print(f"[{__name__}] Blue Team AI assessing situation for action recommendation.")
    time.sleep(random.uniform(0.3, 1.0))

    action = "Monitor passively"
    reason = "Situation appears stable, no immediate threats detected."

    if current_situation.get("high_alerts", 0) > 5:
        action = "Increase monitoring, prepare for incident response."
        reason = "Multiple high-severity alerts detected recently."
    elif current_situation.get("critical_vulnerabilities_exposed", False):
        action = "Prioritize patching, enable IPS/IDS blocking."
        reason = "Critical vulnerabilities are exposed externally."

    recommendation = {
        "action": action,
        "reason": reason,
        "confidence": round(random.uniform(0.8, 0.95), 2)
    }
    print(f"[{__name__}] Blue Team AI action recommendation provided: {action}")
    return recommendation

if __name__ == "__main__":
    # Example usage for local testing
    critical_threat = {
        "type": "Malware Infection",
        "severity": "critical",
        "source_ip": "185.23.4.12",
        "details": "Ransomware detected on internal server."
    }

    print(f"--- Testing Blue Team AI Personality (Analyze Threat) ---")
    threat_analysis = analyze_threat(critical_threat)
    print(json.dumps(threat_analysis, indent=2))
    print("-------------------------------------------------------")

    current_status = {
        "high_alerts": 7,
        "critical_vulnerabilities_exposed": True,
        "network_traffic_spikes": 3
    }
    print(f"\n--- Testing Blue Team AI Personality (Recommend Action) ---")
    action_recommendation = recommend_action(current_status)
    print(json.dumps(action_recommendation, indent=2))
    print("--------------------------------------------------------")
