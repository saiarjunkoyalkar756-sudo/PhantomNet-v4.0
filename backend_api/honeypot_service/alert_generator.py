# backend_api/honeypot_service/alert_generator.py
import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
from .models import HoneypotAlert

async def generate_alerts(enriched_event: Dict[str, Any]) -> List[HoneypotAlert]:
    """
    Generates security alerts based on an enriched honeypot event.
    This is a placeholder for SOAR playbook integration.
    """
    alerts: List[HoneypotAlert] = []

    # Example: Generate an alert for SSH authentication attempts
    if enriched_event.get("event_type") == "auth_attempt" and enriched_event.get("protocol") == "ssh":
        # Further conditions could be added here, e.g.,
        # - multiple failed attempts from the same IP (requires stateful tracking)
        # - known malicious IP from threat intelligence (enriched_event["enriched_data"]["threat_intel"]["is_malicious"])
        
        # For MVP, just alert on any SSH auth attempt
        alert = HoneypotAlert(
            alert_id=str(uuid4()),
            timestamp=datetime.datetime.utcnow().isoformat(),
            honeypot_id=enriched_event["honeypot_id"],
            alert_type="ssh_auth_attempt",
            severity="medium",
            description=f"SSH authentication attempt from {enriched_event['source_ip']}",
            source_ip=enriched_event["source_ip"],
            event_data=enriched_event, # Store the full event data
            enriched_data=enriched_event.get("enriched_data", {})
        )
        alerts.append(alert)
    
    # Example: Alert on detected malicious activity
    if enriched_event.get("enriched_data", {}).get("threat_intel", {}).get("is_malicious"):
        alert = HoneypotAlert(
            alert_id=str(uuid4()),
            timestamp=datetime.datetime.utcnow().isoformat(),
            honeypot_id=enriched_event["honeypot_id"],
            alert_type="malicious_ip_interaction",
            severity="high",
            description=f"Interaction from known malicious IP: {enriched_event['source_ip']}",
            source_ip=enriched_event["source_ip"],
            event_data=enriched_event, # Store the full event data
            enriched_data=enriched_event.get("enriched_data", {})
        )
        alerts.append(alert)

    return alerts