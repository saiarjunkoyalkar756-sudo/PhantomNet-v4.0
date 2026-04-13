import asyncio
import logging
import json
import os
import uuid
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from ..autonomous_blue_team.app import (
    ACTION_HISTORY_DIR,
    auto_block_ip,
    auto_isolate_host,
    auto_reverse_changes,
    auto_kill_process,
    auto_lock_account,
)
from core_config import SAFE_MODE

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = os.getenv('BLUE_TEAM_KAFKA_TOPIC', 'alerts')
GROUP_ID = os.getenv('BLUE_TEAM_KAFKA_GROUP_ID', 'blue-team-group')

ACTION_MAP = {
    "auto_block_ip": auto_block_ip,
    "auto_isolate_host": auto_isolate_host,
    "auto_reverse_changes": auto_reverse_changes,
    "auto_kill_process": auto_kill_process,
    "auto_lock_account": auto_lock_account,
}

async def _process_alert_async(alert: dict):
    """Asynchronous part of alert processing."""
    try:
        logger.info(f"Autonomous Blue Team received alert: {alert.get('alert_name')} (ID: {alert.get('alert_id')})")

        action_type = None
        target = None
        reason = f"Alert: {alert.get('alert_name')}"
        alert_id = alert.get("alert_id") or str(uuid.uuid4())

        if alert.get("alert_name") == "Ransomware Detected":
            action_type = "auto_isolate_host"
            target = alert.get("event_data", {}).get("hostname")
        elif alert.get("alert_name") == "Brute Force Attack":
            action_type = "auto_block_ip"
            target = alert.get("event_data", {}).get("source_ip")
        elif alert.get("alert_name") == "Malware Execution":
            action_type = "auto_kill_process"
            target = alert.get("event_data", {}).get("process_id")

        if action_type and target:
            action_func = ACTION_MAP.get(action_type)
            if action_func:
                action_id = str(uuid.uuid4())
                result_file = os.path.join(ACTION_HISTORY_DIR, f"{action_id}.json")
                action_func(action_id, target, reason, alert_id, result_file)
            else:
                logger.warning(f"No corresponding action function found for action type: {action_type}")
        else:
            logger.info(f"No automated action triggered for alert: {alert.get('alert_name')}")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)

async def start_kafka_consumer():
    """Starts the Kafka consumer for the Autonomous Blue Team."""
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Autonomous Blue Team consumer is disabled.")
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

    logger.info("Autonomous Blue Team: Waiting for alerts...")
    try:
        for message in consumer:
            try:
                alert = message.value
                await _process_alert_async(alert)
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
