from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import datetime

# Assuming these imports from other services for data retrieval
# In a real scenario, these would be API calls to respective microservices
from backend_api.siem_ingest_service import crud as siem_crud
from backend_api.vulnerability_management_service import crud as vuln_crud

async def build_alert_context(
    alert_id: Optional[str] = None,
    event_id: Optional[str] = None,
    query: Optional[str] = None,
    siem_db: Session = None, # Dependency injection for SIEM DB
    vuln_db: Session = None # Dependency injection for Vulnerability DB
) -> Dict[str, Any]:
    """
    Gathers relevant context for an alert or event from various services.
    This function simulates retrieving data from SIEM, Vulnerability Management, etc.
    """
    context = {
        "primary_alert_id": alert_id,
        "primary_event_id": event_id,
        "natural_language_query": query,
        "primary_event": None,
        "related_events": [],
        "related_vulnerabilities": [],
        "related_assets": [],
        "additional_context": {}
    }

    # Simulate retrieving a primary event if an event_id or alert_id (which maps to an event) is given
    if event_id and siem_db:
        # Assuming event_id here refers to RawLogEvent.id or NormalizedEvent.event_id
        # For simplicity, let's try to get a RawLogEvent
        primary_event = siem_crud.get_raw_log_event(siem_db, log_id=int(event_id))
        if primary_event:
            context["primary_event"] = primary_event
            # Try to find related events from the same host/timeframe
            context["related_events"] = siem_crud.get_raw_log_events(
                siem_db, 
                host_identifier=primary_event.host_identifier, 
                start_time=primary_event.timestamp - datetime.timedelta(minutes=5), 
                end_time=primary_event.timestamp + datetime.timedelta(minutes=5),
                limit=10 # Limit related events
            )
            # Remove primary event from related events list
            context["related_events"] = [e for e in context["related_events"] if e.id != primary_event.id]

            # Try to get related asset and vulnerabilities
            if primary_event.host_identifier and vuln_db:
                related_asset = vuln_crud.get_asset(vuln_db, asset_id=primary_event.host_identifier)
                if related_asset:
                    context["related_assets"].append(related_asset)
                    context["related_vulnerabilities"] = vuln_crud.get_vulnerabilities(vuln_db, asset_id=related_asset.id)
    
    # Add more logic here to fetch context from other services (e.g., threat intelligence, asset inventory)
    # based on the alert_id or parsed query.

    return context
