from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.dna_engine import DNAEngine
from backend_api.shared.health_utils import check_kafka_health, perform_full_health_check, check_kafka_consumer_health
from backend_api.core.response import success_response, error_response
from loguru import logger
import json
import os
import asyncio
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from uuid import UUID
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
SOURCE_TOPIC = 'telemetry-events'
DESTINATION_TOPIC = 'normalized-events'
GROUP_ID = 'event-normalizer-group'

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# --- Initialize Engines ---
dna_engine = DNAEngine()

# --- Global State ---
stop_processing_event = asyncio.Event()

def normalize_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalization logic with Genetic Provenance Tagging.
    """
    event_data['normalized_at'] = datetime.now(timezone.utc).isoformat()
    event_data['platform_schema_version'] = '1.0.0'
    
    tenant_id_str = event_data.get('tenant_id')
    event_data['tenant_id'] = str(UUID(tenant_id_str)) if tenant_id_str else str(DEFAULT_TENANT_ID)
    
    # Tag event with hardware-bound DNA
    event_data = dna_engine.tag_event(event_data)
    
    return event_data

async def consume_and_process_kafka_messages():
    logger.info("Starting Kafka consumer for event normalization...")
    await asyncio.sleep(10) # Startup delay

    try:
        consumer = KafkaConsumer(
            SOURCE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka consumer/producer initialized.")
    except Exception as e:
        logger.error(f"Kafka connection failed: {e}")
        return

    try:
        for message in consumer:
            if stop_processing_event.is_set():
                break

            try:
                raw_event = message.value
                normalized_event = normalize_event(raw_event)
                logger.info(f"Normalized event: {normalized_event.get('event_id')} type={normalized_event.get('event_type')}")
                producer.send(DESTINATION_TOPIC, normalized_event)
            except Exception as e:
                logger.error(f"Error normalizing event: {e}")
    except asyncio.CancelledError:
        logger.info("Normalizer loop cancelled.")
    finally:
        consumer.close()
        producer.close()
        logger.info("Event Normalizer backend resources closed.")

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
