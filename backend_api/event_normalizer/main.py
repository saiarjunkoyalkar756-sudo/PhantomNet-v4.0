import json
import os
import signal
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from uuid import UUID # Import UUID
import logging # Import standard logging module
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio

from backend_api.shared.logger_config import setup_logging # Import shared logger setup
from backend_api.shared.health_utils import check_kafka_health, perform_full_health_check # Import health_utils

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
SOURCE_TOPIC = 'telemetry-events'
DESTINATION_TOPIC = 'normalized-events'
GROUP_ID = 'event-normalizer-group'
APP_PORT = int(os.environ.get('APP_PORT', '8002')) # New port for this service

# Default tenant ID for events if not provided by the agent/ingestor
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# --- Setup Logging ---
logger = setup_logging(name="event_normalizer", level=logging.INFO)

# --- Global Kafka Instances ---
consumer: Optional[KafkaConsumer] = None
producer: Optional[KafkaProducer] = None
consumer_task: Optional[asyncio.Task] = None
stop_processing_event = asyncio.Event()


def normalize_event(event_data):
    """
    This is where you would put your complex normalization logic.
    For now, we'll just add a normalization timestamp and ensure tenant_id.
    """
    event_data['normalized_at'] = datetime.now(timezone.utc).isoformat()
    event_data['platform_schema_version'] = '1.0.0'
    
    # Extract tenant_id from incoming event or use default
    tenant_id_str = event_data.get('tenant_id')
    event_data['tenant_id'] = str(UUID(tenant_id_str)) if tenant_id_str else str(DEFAULT_TENANT_ID)
    
    return event_data

async def consume_and_process_kafka_messages():
    global consumer, producer
    logger.info("Starting Kafka consumer for event normalization...")

    # It can take a few seconds for the Kafka broker to be ready.
    # In a real K8s environment, you'd use readiness probes.
    await asyncio.sleep(10) # Give Redpanda time to start

    try:
        consumer = KafkaConsumer(
            SOURCE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info("Kafka consumer initialized successfully.")

        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka producer initialized successfully.")

    except Exception as e:
        logger.error(f"Could not connect to Kafka: {e}", exc_info=True)
        # This will allow lifespan to continue, but health check will fail
        return

    logger.info("Event Normalizer started. Polling for messages...")
    try:
        for message in consumer:
            if stop_processing_event.is_set():
                break # Exit loop if shutdown is requested

            try:
                raw_event = message.value
                logger.debug(f"Received event: {raw_event}")

                normalized_event = normalize_event(raw_event)
                logger.info(f"Publishing normalized event for tenant {normalized_event.get('tenant_id')} event_type {normalized_event.get('event_type')}", extra=normalized_event)

                producer.send(DESTINATION_TOPIC, normalized_event)

            except json.JSONDecodeError:
                logger.error(f"Could not decode message: {message.value}")
            except Exception as e:
                logger.error(f"An error occurred during event processing: {e}", exc_info=True)
    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled.")
    except Exception as e:
        logger.error(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
    finally:
        logger.info("Kafka consumer loop finished.")
        if consumer is not None:
            consumer.close()
            logger.info("Kafka consumer closed.")
        if producer is not None:
            producer.close()
            logger.info("Kafka producer closed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Event Normalizer service starting up...")
    global consumer_task
    consumer_task = asyncio.create_task(consume_and_process_kafka_messages())
    logger.info("Kafka consumer background task initiated.")
    
    yield
    
    # Shutdown logic
    logger.info("Event Normalizer service shutting down.")
    stop_processing_event.set() # Signal consumer to stop
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Kafka consumer task cancelled during shutdown.")
    
    logger.info("Event Normalizer service stopped.")


app = FastAPI(
    title="Event Normalizer",
    description="Consumes raw telemetry, normalizes it, and publishes to a new topic.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """
    Returns the comprehensive health status of the Event Normalizer service and its Kafka dependencies.
    """
    kafka_status = await check_kafka_health()
    kafka_consumer_status = await check_kafka_consumer_health(SOURCE_TOPIC, GROUP_ID)
    
    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "kafka_consumer": kafka_consumer_status
    })
    
    if full_status["status"] == "healthy":
        logger.info("Event Normalizer is healthy.", extra=full_status)
    else:
        logger.warning("Event Normalizer is in a degraded state.", extra=full_status)
        
    return full_status
