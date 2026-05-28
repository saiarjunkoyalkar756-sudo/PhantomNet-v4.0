import asyncio
import logging
import json
import os
import time

from backend_api.shared.kafka_topics import RAW_TELEMETRY, ALERTS
from backend_api.shared.kafka_client import ResilientKafkaConsumer, ResilientKafkaProducer
from .database import insert_event, create_events_table
from core_config import SAFE_MODE

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC_IN = os.getenv('ESP_KAFKA_TOPIC_IN', RAW_TELEMETRY)
KAFKA_TOPIC_OUT = os.getenv('ESP_KAFKA_TOPIC_OUT', ALERTS)
GROUP_ID = os.getenv('ESP_KAFKA_GROUP_ID', 'event-stream-processor-group')
producer = None

def normalize_event(raw_event):
    """Transforms a raw log event into a standardized format."""
    normalized = {
        "timestamp": raw_event.get("timestamp", time.time()),
        "source": "phantomnet_agent",
        "event_type": "log",
        "raw_event": raw_event,
        "source_ip": raw_event.get("source_ip"),
        "destination_ip": raw_event.get("destination_ip"),
        "protocol": raw_event.get("protocol"),
        "details": raw_event.get("details", {}),
    }
    return normalized

def check_for_alert(normalized_event):
    """Checks if a normalized event should trigger an alert."""
    if "error" in normalized_event.get("details", {}).get("message", "").lower():
        return {
            "alert_name": "Error Detected in Log",
            "severity": "low",
            "event_data": normalized_event,
        }
    return None

def process_event(raw_event):
    """Processes a raw event, normalizes it, inserts to database, and triggers alerts if necessary."""
    try:
        normalized_event = normalize_event(raw_event)
        logger.info(f"Normalized event: {normalized_event}")
        insert_event(normalized_event)
        alert = check_for_alert(normalized_event)
        if alert and producer:
            producer.send(KAFKA_TOPIC_OUT, alert)
            logger.info(f"Published alert: {alert['alert_name']}")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise  # Re-raise exception to let ResilientKafkaConsumer trigger DLQ logic

async def start_kafka_consumer():
    """Starts the resilient Kafka consumer for the Event Stream Processor."""
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Event Stream Processor consumer is disabled.")
        return

    create_events_table()
    
    global producer
    producer = ResilientKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    
    consumer = ResilientKafkaConsumer(
        topic=KAFKA_TOPIC_IN,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        dlq_topic=f"{KAFKA_TOPIC_IN}.dlq"
    )
    
    logger.info("Event Stream Processor: Waiting for messages...")
    loop = asyncio.get_running_loop()
    # Run the listener in a background thread executor as it contains blocking IO loops
    await loop.run_in_executor(None, consumer.listen, process_event)
