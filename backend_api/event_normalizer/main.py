from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.dna_engine import DNAEngine
from backend_api.shared.health_utils import check_kafka_health, perform_full_health_check, check_kafka_consumer_health
from backend_api.core.response import success_response, error_response
from loguru import logger
import json
import os
import asyncio
from datetime import datetime, timezone
from backend_api.shared.kafka_topics import RAW_TELEMETRY as SOURCE_TOPIC, NORMALIZED_EVENTS as DESTINATION_TOPIC
from backend_api.shared.kafka_client import ResilientKafkaConsumer, ResilientKafkaProducer
from backend_api.core_config import SAFE_MODE
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from phantomnet_core.contracts import CONTRACT_VERSION, EventEnvelope

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
GROUP_ID = 'event-normalizer-group'

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# --- Initialize Engines ---
dna_engine = DNAEngine()

# --- Global State ---
stop_processing_event = asyncio.Event()
producer = None

def normalize_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalization logic with Genetic Provenance Tagging.
    """
    tenant_id_str = event_data.get("tenant_id")
    tenant_id = str(UUID(tenant_id_str)) if tenant_id_str else str(DEFAULT_TENANT_ID)
    envelope = EventEnvelope(
        schema_version=CONTRACT_VERSION,
        event_id=str(event_data.get("event_id") or event_data.get("id") or uuid4()),
        timestamp=event_data.get("timestamp", datetime.now(timezone.utc)),
        tenant_id=tenant_id,
        source=str(event_data.get("source", "unknown")),
        event_type=str(event_data.get("event_type", "generic_event")),
        severity=str(event_data.get("severity", "informational")).lower(),
        payload=event_data.get("payload", event_data),
        correlation_id=event_data.get("correlation_id"),
        trace_id=event_data.get("trace_id"),
        tags=event_data.get("tags", []),
        provenance={
            **event_data.get("provenance", {}),
            "normalizer": "event-normalizer",
            "legacy_schema_version": event_data.get("platform_schema_version"),
        },
    )
    normalized_event = envelope.model_dump(mode="json")
    normalized_event["normalized_at"] = datetime.now(timezone.utc).isoformat()
    normalized_event["platform_schema_version"] = CONTRACT_VERSION

    # Tag event with hardware-bound DNA after normalization.
    return dna_engine.tag_event(normalized_event)

def process_event(raw_event: Dict[str, Any]):
    """Processes a single telemetry event, normalizes it, and sends it to the destination topic."""
    try:
        normalized_event = normalize_event(raw_event)
        logger.info(f"Normalized event: {normalized_event.get('event_id')} type={normalized_event.get('event_type')}")
        if producer:
            producer.send(DESTINATION_TOPIC, normalized_event)
    except Exception as e:
        logger.error(f"Error normalizing event: {e}")
        raise  # Re-raise exception to let ResilientKafkaConsumer trigger DLQ logic

async def consume_and_process_kafka_messages():
    logger.info("Starting Kafka consumer for event normalization...")
    await asyncio.sleep(10) # Startup delay

    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Event Normalizer consumer is disabled.")
        return

    global producer
    try:
        producer = ResilientKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        consumer = ResilientKafkaConsumer(
            topic=SOURCE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=GROUP_ID,
            dlq_topic=f"{SOURCE_TOPIC}.dlq"
        )
        logger.info("Kafka consumer/producer initialized.")
    except Exception as e:
        logger.error(f"Kafka connection failed: {e}")
        return

    logger.info("Event Normalizer: Waiting for messages...")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, consumer.listen, process_event)

async def event_normalizer_startup(app: FastAPI):
    app.state.consumer_task = asyncio.create_task(consume_and_process_kafka_messages())
    logger.info("Event Normalizer: Background consumer task started.")

async def event_normalizer_shutdown(app: FastAPI):
    if hasattr(app.state, "consumer_task"):
        stop_processing_event.set()
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Event Normalizer: Background consumer task stopped.")

app = create_phantom_service(
    name="Event Normalizer",
    description="Normalized raw telemetry against PhantomNet schemas.",
    version="1.0.0",
    custom_startup=event_normalizer_startup,
    custom_shutdown=event_normalizer_shutdown
)

@app.get("/health_detailed")
async def health_detailed():
    """
    Returns the comprehensive health status of the Event Normalizer.
    """
    kafka_status = await check_kafka_health()
    kafka_consumer_status = await check_kafka_consumer_health(SOURCE_TOPIC, GROUP_ID)
    
    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "kafka_consumer": kafka_consumer_status
    })
    
    return success_response(data=full_status)
