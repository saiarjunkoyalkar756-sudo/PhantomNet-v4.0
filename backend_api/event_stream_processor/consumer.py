import asyncio
import logging
import json
import os
import time
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

from .database import insert_event, create_events_table
from core_config import SAFE_MODE

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC_IN = os.getenv('ESP_KAFKA_TOPIC_IN', 'attack_logs')
KAFKA_TOPIC_OUT = os.getenv('ESP_KAFKA_TOPIC_OUT', 'alerts')
GROUP_ID = os.getenv('ESP_KAFKA_GROUP_ID', 'event-stream-processor-group')

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

async def start_kafka_consumer():
    """Starts the Kafka consumer for the Event Stream Processor."""
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Event Stream Processor consumer is disabled.")
        return

    consumer = None
    producer = None
    while not consumer or not producer:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC_IN,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=GROUP_ID,
                auto_offset_reset='earliest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Successfully connected to Kafka.")
        except NoBrokersAvailable:
            logger.error(f"Could not connect to Kafka at {KAFKA_BOOTSTRAP_SERVERS}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

    create_events_table()
    logger.info("Event Stream Processor: Waiting for messages...")
    try:
        for message in consumer:
            try:
                raw_event = message.value
                normalized_event = normalize_event(raw_event)
                logger.info(f"Normalized event: {normalized_event}")
                insert_event(normalized_event)
                alert = check_for_alert(normalized_event)
                if alert:
                    producer.send(KAFKA_TOPIC_OUT, alert)
                    logger.info(f"Published alert: {alert['alert_name']}")
            except json.JSONDecodeError:
                logger.error(f"Failed to decode Kafka message as JSON: {message.value}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
        if producer:
            producer.close()
        logger.info("Kafka consumer and producer stopped.")
