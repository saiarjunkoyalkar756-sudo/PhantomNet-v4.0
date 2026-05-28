import asyncio
import logging
import json
import os
import time

from ..ai_behavioral_engine.app import (
    BehavioralEvent,
    analyze_behavioral_event,
)
from core_config import SAFE_MODE
from backend_api.shared.kafka_topics import TOPICS
from backend_api.shared.kafka_client import ResilientKafkaConsumer

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = os.getenv('BEHAVIORAL_KAFKA_TOPIC', TOPICS["NORMALIZED_EVENTS"])
GROUP_ID = os.getenv('BEHAVIORAL_KAFKA_GROUP_ID', 'behavioral-engine-group')


def _process_event_sync(event_data: dict):
    """Synchronous processing callback for resilient consumer."""
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

        # Note: analyze_behavioral_event is an async function in app.py.
        # But we can run it using asyncio.run or schedule it on the loop.
        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(analyze_behavioral_event(event), loop)
            future.result()
        except RuntimeError:
            asyncio.run(analyze_behavioral_event(event))
            
        logger.info(f"Analysis complete for {event.event_id}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise  # Re-raise to trigger DLQ logic


async def start_kafka_consumer():
    """Starts the resilient Kafka consumer for the AI Behavioral Engine."""
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. AI Behavioral Engine consumer is disabled.")
        return

    consumer = ResilientKafkaConsumer(
        topic=KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        dlq_topic=f"{KAFKA_TOPIC}.dlq"
    )

    logger.info("AI Behavioral Engine: Waiting for messages...")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, consumer.listen, _process_event_sync)
