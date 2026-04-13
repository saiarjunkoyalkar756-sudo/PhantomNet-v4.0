import asyncio
import logging
import json
import httpx
import os
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from .database import get_all_rules
from backend_api.threat_intelligence_service.enrichment import ThreatIntelligenceEnricher
from core_config import SAFE_MODE

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = os.getenv('CORRELATION_KAFKA_TOPIC', 'attack_logs')
GROUP_ID = os.getenv('CORRELATION_KAFKA_GROUP_ID', 'correlation-engine-group')

# --- Service URLs ---
MITRE_MAPPER_URL = "http://mitre_attack_mapper:8000"

# --- Global Instances ---
ti_enricher = ThreatIntelligenceEnricher()

async def map_event_with_mitre(event: dict) -> list:
    """Calls the MITRE ATT&CK Mapper service to map an event to techniques."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MITRE_MAPPER_URL}/map", json={"event": event})
            response.raise_for_status()
            return response.json().get("techniques", [])
    except httpx.RequestError as e:
        logger.error(f"Could not connect to MITRE ATT&CK Mapper service: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error mapping event with MITRE ATT&CK Mapper: {e.response.status_code} {e.response.text}")
    except Exception as e:
        logger.error(f"An unexpected error during MITRE mapping: {e}", exc_info=True)
    return []

async def _process_event_async(event: dict):
    """Asynchronous part of event processing in the correlation engine."""
    # 1. Map event to MITRE ATT&CK techniques
    mapped_techniques = await map_event_with_mitre(event)
    if mapped_techniques:
        logger.info(f"Event mapped to MITRE techniques: {mapped_techniques}")
        event["mitre_techniques"] = mapped_techniques

    # 2. Enrich indicators in the event using Threat Intelligence Service
    if event.get("source_ip"):
        ti_result = await ti_enricher.enrich_indicator(event["source_ip"], "ip")
        if ti_result and ti_result.is_malicious:
            logger.warning(f"Event involves malicious IP: {event['source_ip']} (Provider: {ti_result.threat_scores[0].provider if ti_result.threat_scores else 'N/A'})")
            event["ti_enrichment"] = ti_result.model_dump()
            event["is_malicious_ip"] = True

    # 3. Load rules dynamically and apply them
    rules = get_all_rules()
    for rule in rules:
        try:
            if rule["logic"].get("keyword") and rule["logic"]["keyword"] in str(event):
                logger.warning(f"Rule '{rule['name']}' matched! Action: {rule['action']}")
                # In a real system, this would trigger an actual action
        except Exception as e:
            logger.error(f"Error applying rule '{rule['name']}': {e}")

async def start_kafka_consumer():
    """Starts the Kafka consumer for the correlation engine."""
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Correlation engine consumer is disabled.")
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

    logger.info("Correlation engine waiting for messages...")
    try:
        for message in consumer:
            try:
                event = message.value
                logger.info(f"Received event: {event}")
                await _process_event_async(event)
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
