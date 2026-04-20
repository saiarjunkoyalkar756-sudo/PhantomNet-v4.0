from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.health_utils import check_kafka_health, perform_full_health_check
from backend_api.core.response import success_response, error_response
from loguru import logger
from kafka import KafkaProducer
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
import json
import os
from fastapi import FastAPI, HTTPException, Request

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
TELEMETRY_TOPIC = 'telemetry-events'
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# --- Global State ---
producer: Optional[KafkaProducer] = None

def get_kafka_producer():
    global producer
    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Kafka producer initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    return producer

class TelemetryEvent(BaseModel):
    agent_id: str
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    tenant_id: UUID = DEFAULT_TENANT_ID

async def telemetry_ingestor_startup(app: FastAPI):
    """
    Handles startup events for the Telemetry Ingestor.
    """
    try:
        get_kafka_producer()
    except Exception:
        logger.error("Failed to initialize Kafka producer on startup.")

async def telemetry_ingestor_shutdown(app: FastAPI):
    """
    Handles shutdown events for the Telemetry Ingestor.
    """
    global producer
    if producer is not None:
        producer.close()
        logger.info("Kafka producer closed.")

app = create_phantom_service(
    name="Telemetry Ingestor",
    description="Receives telemetry data from PhantomNet agents and publishes it to the event bus.",
    version="1.0.0",
    custom_startup=telemetry_ingestor_startup,
    custom_shutdown=telemetry_ingestor_shutdown
)

@app.post("/ingest")
async def ingest_telemetry(event: TelemetryEvent):
    """
    Ingest a single telemetry event from an agent.
    """
    try:
        kafka_producer = get_kafka_producer()
        kafka_producer.send(TELEMETRY_TOPIC, event.model_dump())
        logger.info(f"Ingested event from agent {event.agent_id} for tenant {event.tenant_id}")
        return success_response(message="Event ingested successfully.")
    except Exception as e:
        logger.error(f"Error ingesting telemetry event: {e}")
        return error_response(code="INGESTION_FAILED", message=str(e), status_code=500)

@app.get("/health_detailed")
async def health_detailed():
    """
    Returns the comprehensive health status of the Telemetry Ingestor.
    """
    kafka_status = await check_kafka_health()
    full_status = await perform_full_health_check({"kafka_broker": kafka_status})
    return success_response(data=full_status)
