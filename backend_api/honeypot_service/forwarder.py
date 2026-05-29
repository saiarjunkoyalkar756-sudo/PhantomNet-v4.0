# backend_api/honeypot_service/forwarder.py
import json
import logging
from typing import Dict, Any
from .event_normalizer import normalize_event # Import the event normalizer
from .event_enricher import enrich_event # Import the event enricher
from .alert_generator import generate_alerts # Import the alert generator

logger = logging.getLogger(__name__)

async def forward_event(event: Dict[str, Any]):
    """
    Forwards a normalized honeypot event to the message bus or telemetry ingest.
    For now, it just prints the event and any generated alerts.
    """
    normalized_event = normalize_event(event) # Normalize the event
    enriched_event = await enrich_event(normalized_event) # Enrich the normalized event
    
    logger.info(f"Forwarding enriched event: {json.dumps(enriched_event, indent=2)}")
    # In a real implementation, this would send the enriched event to Kafka, Redis, or another telemetry system.
    # e.g., await message_bus.publish("honeypot_events", enriched_event)

    generated_alerts = await generate_alerts(enriched_event)
    for alert in generated_alerts:
        logger.warning(f"Generated honeypot alert: {json.dumps(alert.dict(), indent=2)}")
        # In a real implementation, this would send the alert to a SOAR platform or a dedicated alert topic.
        # e.g., await message_bus.publish("honeypot_alerts", alert.dict())
