import asyncio
import logging
import json
import os
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import time

from ..ai_behavioral_engine.app import (
    BehavioralEvent,
    analyze_behavioral_event,
)
from core_config import SAFE_MODE

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = os.getenv('BEHAVIORAL_KAFKA_TOPIC', 'attack_logs')
GROUP_ID = os.getenv('BEHAVIORAL_KAFKA_GROUP_ID', 'behavioral-engine-group')


async def _process_event_async(event_data: dict):
    """Asynchronous part of event processing."""
    try:
        logger.info(f"Received event for behavioral analysis: {event_data.get('event_id', 'N/A')}")

        event = BehavioralEvent(
            event_id=event_data.get("event_id", str(time.time())),
            event_type=event_data.get("event_type", "unknown"),
            source_ip=event_data.get("source_ip", "0.0.0.0"),
            user_id=event_data.get("user_id"),
            entity_id=event_data.get("entity_id"),
            timestamp=event_data.get("timestamp", time.time()),
            data=event_data,
        )

        analysis_results = analyze_behavioral_event(event)
        logger.info(f"Analysis results for {event.event_id}: {analysis_results}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)


async def start_kafka_consumer():
    """Starts the Kafka consumer for the AI Behavioral Engine."""
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. AI Behavioral Engine consumer is disabled.")
        return

    consumer = None
    while not consumer:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=GROUP_ID,
                auto_offset_reset='earliest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Successfully connected to Kafka.")
        except NoBrokersAvailable:
            logger.error(f"Could not connect to Kafka at {KAFKA_BOOTSTRAP_SERVERS}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

    logger.info("AI Behavioral Engine: Waiting for messages...")
    try:
        for message in consumer:
            try:
                event_data = message.value
                await _process_event_async(event_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode Kafka message as JSON: {message.value}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    except Exception as e:
        logger.critical(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
        logger.info("Kafka consumer stopped.")
