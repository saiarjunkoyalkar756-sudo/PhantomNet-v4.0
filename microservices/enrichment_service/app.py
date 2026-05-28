# microservices/enrichment_service/app.py
import sys
import os
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
from loguru import logger
from fastapi import FastAPI

# Append workspace root to path to load shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend_api.shared.kafka_topics import NORMALIZED_EVENTS, ENRICHED_EVENTS
from backend_api.shared.kafka_client import ResilientKafkaConsumer, ResilientKafkaProducer
from backend_api.core_config import SAFE_MODE
from backend_api.core.response import success_response

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
GROUP_ID = 'enrichment-service-group'

app = FastAPI(
    title="Threat Intelligence Enrichment Service",
    description="Enriches normalized telemetry with active threat intelligence data.",
    version="1.0.0"
)

# Global State
producer = None
stop_processing_event = asyncio.Event()

def enrich_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriches telemetry events with threat intelligence data.
    """
    enriched = event.copy()
    enriched["enriched_at"] = datetime.now(timezone.utc).isoformat()
    
    # Mock threat intelligence database check
    source_ip = event.get("source_ip") or event.get("ip")
    details = event.get("details") or {}
    message = details.get("message", "").lower()
    
    # Highlight known malicious payloads or target simulation IPs
    if source_ip in ["192.168.1.100", "8.8.8.8"] or "eternalblue" in message or "malicious" in message:
        enriched["threat_intel"] = {
            "is_malicious": True,
            "threat_score": 95,
            "feed_source": "PhantomNet Global Threat Feed",
            "actor": "APT-41 (Red Team Simulation)",
            "category": "Command & Control / Exploitation",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        logger.warning(f"Malicious indicator detected! Enriched event {event.get('event_id')} from {source_ip}")
    else:
        enriched["threat_intel"] = {
            "is_malicious": False,
            "threat_score": 5,
            "feed_source": "PhantomNet Global Threat Feed",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Telemetry event {event.get('event_id')} enriched with clean threat intel.")
        
    return enriched

def process_event(raw_event: Dict[str, Any]):
    """Processes, enriches and forwards the event to the enriched topic."""
    try:
        enriched = enrich_event(raw_event)
        if producer:
            producer.send(ENRICHED_EVENTS, enriched)
    except Exception as e:
        logger.error(f"Error enriching event: {e}")
        raise  # Re-raise to trigger ResilientKafkaConsumer DLQ routing

async def consume_and_process_messages():
    logger.info("Starting Threat Intelligence Enrichment Service consumer...")
    await asyncio.sleep(5)  # Short startup delay

    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Ingestion and enrichment loop is disabled.")
        return

    global producer
    try:
        producer = ResilientKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        consumer = ResilientKafkaConsumer(
            topic=NORMALIZED_EVENTS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=GROUP_ID,
            dlq_topic=f"{NORMALIZED_EVENTS}.dlq"
        )
        logger.info("Enrichment Service: Kafka producer/consumer initialized.")
    except Exception as e:
        logger.error(f"Enrichment Service Kafka connection failed: {e}")
        return

    logger.info("Enrichment Service: Listening for normalized events...")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, consumer.listen, process_event)

@app.on_event("startup")
async def startup_event():
    app.state.consumer_task = asyncio.create_task(consume_and_process_messages())
    logger.info("Enrichment Service startup sequence complete.")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "consumer_task"):
        stop_processing_event.set()
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Enrichment Service shutdown complete.")

@app.get("/")
def read_root():
    return {"status": "operational", "service": "threat-intelligence-enrichment"}
