import json
import os
import signal
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from uuid import UUID
import logging
from backend_api.shared.logger_config import setup_logging

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
SOURCE_TOPIC = 'telemetry-events'
DESTINATION_TOPIC = 'normalized-events'
GROUP_ID = 'event-normalizer-group'
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
SAFE_MODE = False

# --- Setup Logging ---
logger = setup_logging(name="event_normalizer", level=logging.INFO)

# --- Main Application Logic ---
logger.info("Starting Event Normalizer Service...")
logger.info(f"Kafka Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")

consumer = None
producer = None

def initialize_kafka():
    global consumer, producer, SAFE_MODE
    try:
        if consumer:
            consumer.close()
        if producer:
            producer.close()

        consumer = KafkaConsumer(
            SOURCE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=1000 # To prevent blocking indefinitely
        )
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka consumer and producer initialized successfully.")
        SAFE_MODE = False
        return True
    except NoBrokersAvailable:
        logger.error("Could not connect to Kafka: No brokers available. Entering SAFE_MODE.")
        SAFE_MODE = True
        return False
    except Exception as e:
        logger.error(f"Could not connect to Kafka: {e}", exc_info=True)
        SAFE_MODE = True
        return False

def normalize_event(event_data):
    """
    This is where you would put your complex normalization logic.
    For now, we'll just add a normalization timestamp and ensure tenant_id.
    """
    event_data['normalized_at'] = datetime.now(timezone.utc).isoformat()
    event_data['platform_schema_version'] = '1.0.0'
    
    tenant_id_str = event_data.get('tenant_id')
    event_data['tenant_id'] = str(UUID(tenant_id_str)) if tenant_id_str else str(DEFAULT_TENANT_ID)
    
    return event_data

def handle_shutdown(signum, frame):
    """Graceful shutdown."""
    logger.info("Shutdown signal received. Closing Kafka connections...")
    if consumer is not None:
        consumer.close()
        logger.info("Kafka consumer closed.")
    if producer is not None:
        producer.close()
        logger.info("Kafka producer closed.")
    exit(0)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

while True:
    if not initialize_kafka():
        logger.info("Retrying Kafka connection in 30 seconds...")
        time.sleep(30)
        continue

    logger.info("Event Normalizer started. Polling for messages...")
    for message in consumer:
        try:
            raw_event = message.value
            logger.debug(f"Received event: {raw_event}")

            normalized_event = normalize_event(raw_event)
            logger.info(f"Publishing normalized event for tenant {normalized_event.get('tenant_id')} event_type {normalized_event.get('event_type')}", extra=normalized_event)

            producer.send(DESTINATION_TOPIC, normalized_event)

        except json.JSONDecodeError:
            logger.error(f"Could not decode message: {message.value}")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            # If we have a persistent error with Kafka, re-initialize
            if isinstance(e, (NoBrokersAvailable)):
                break
    
    # If the loop breaks, it means there was an issue, so we wait and retry
    logger.warning("Consumer loop exited, likely due to an error. Re-initializing...")
    time.sleep(10)
