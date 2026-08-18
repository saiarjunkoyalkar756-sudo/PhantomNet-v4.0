import asyncio
import logging
import json
from hashlib import sha256
import httpx
import os
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from .database import get_all_rules
from .alert_workflow import AlertWorkflow
from .detection_store import DetectionRepository
from .ingestion import CanonicalBrokerProcessor, BrokerIngestionResult
from .ingestion_reliability import (
    BrokerDeliveryRecordedError,
    IngestionDeadLetterRepository,
    ReliableCanonicalIngestion,
)
from backend_api.core_config import SAFE_MODE
from backend_api.shared.kafka_topics import NORMALIZED_EVENTS
from phantomnet_core.contracts import BrokerDeliveryMetadata

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = os.getenv("CORRELATION_KAFKA_TOPIC", NORMALIZED_EVENTS)
GROUP_ID = os.getenv('CORRELATION_KAFKA_GROUP_ID', 'correlation-engine-group')

# --- Service URLs ---
MITRE_MAPPER_URL = "http://mitre_attack_mapper:8000"

# --- Global Instances ---
ti_enricher = None
broker_processor = CanonicalBrokerProcessor(
    DetectionRepository(),
    alert_workflow=AlertWorkflow(),
)
dead_letter_repository = IngestionDeadLetterRepository()
reliable_ingestion = ReliableCanonicalIngestion(broker_processor.process, dead_letter_repository)


def get_threat_intelligence_enricher():
    """Lazily initialize optional external enrichment after canonical persistence succeeds."""
    global ti_enricher
    if ti_enricher is None:
        from backend_api.threat_intelligence_service.enrichment import ThreatIntelligenceEnricher
        ti_enricher = ThreatIntelligenceEnricher()
    return ti_enricher

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

async def _process_event_async(
    event: dict,
    delivery: BrokerDeliveryMetadata | None = None,
) -> BrokerIngestionResult:
    """Persist governed detections before optional enrichment; failed broker deliveries retain evidence."""
    ingestion = (
        await reliable_ingestion.process_delivery(event, delivery)
        if delivery is not None
        else await broker_processor.process(event)
    )
    canonical_event = ingestion.event.model_dump(mode="json")
    logger.info(
        "Canonical event accepted",
        event_id=ingestion.event.event_id,
        tenant_id=ingestion.event.tenant_id,
        created_detections=len(ingestion.created_detection_ids),
        duplicate_detections=len(ingestion.duplicate_detection_ids),
    )

    # Optional enrichment augments correlation context; it never dispatches containment.
    mapped_techniques = await map_event_with_mitre(canonical_event)
    if mapped_techniques:
        canonical_event["mitre_techniques"] = mapped_techniques

    payload = canonical_event.get("payload", {})
    source_ip = payload.get("source_ip")
    if source_ip:
        ti_result = await get_threat_intelligence_enricher().enrich_indicator(source_ip, "ip")
        if ti_result and ti_result.is_malicious:
            canonical_event["ti_enrichment"] = ti_result.model_dump()
            canonical_event["is_malicious_ip"] = True

    rules = await get_all_rules()
    for rule in rules:
        try:
            keyword = rule["logic"].get("keyword")
            if keyword and keyword in str(canonical_event):
                logger.warning("Correlation rule matched", rule_name=rule["name"], action=rule["action"])
        except Exception as exc:
            logger.error("Correlation rule evaluation failed", rule_name=rule["name"], error_type=type(exc).__name__)
    return ingestion

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
                enable_auto_commit=False,
                value_deserializer=lambda x: x.decode("utf-8", errors="replace")
            )
            logger.info("Successfully connected to Kafka.")
        except NoBrokersAvailable:
            logger.error(f"Could not connect to Kafka at {KAFKA_BOOTSTRAP_SERVERS}. Retrying in 10 seconds...")
            await asyncio.sleep(10)

    logger.info("Correlation engine waiting for messages...")
    try:
        for message in consumer:
            try:
                delivery = BrokerDeliveryMetadata(
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                )
                event = json.loads(message.value)
                logger.info("Received canonical broker event", topic=delivery.topic, partition=delivery.partition, offset=delivery.offset)
                await _process_event_async(event, delivery)
                consumer.commit()
            except BrokerDeliveryRecordedError as exc:
                logger.error(
                    "Canonical broker delivery was dead-lettered; committing offset after durable receipt.",
                    dead_letter_id=exc.receipt.dead_letter_id,
                    error_code=exc.receipt.error_code,
                )
                consumer.commit()
            except json.JSONDecodeError as exc:
                raw_digest = sha256(message.value.encode("utf-8")).hexdigest()
                delivery = BrokerDeliveryMetadata(topic=message.topic, partition=message.partition, offset=message.offset)
                receipt, _ = await dead_letter_repository.record_failure(
                    {"broker_payload_sha256": raw_digest, "content_type": "invalid_json"},
                    delivery,
                    exc,
                )
                logger.error(
                    "Invalid JSON broker delivery was dead-lettered; committing offset after durable receipt.",
                    dead_letter_id=receipt.dead_letter_id,
                )
                consumer.commit()
            except Exception as exc:
                logger.error(
                    "Canonical broker delivery failed before durable evidence; offset was not committed.",
                    error_type=type(exc).__name__,
                )
    except Exception as e:
        logger.critical(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
        logger.info("Kafka consumer stopped.")
