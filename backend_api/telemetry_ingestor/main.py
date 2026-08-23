from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.health_utils import check_kafka_health, perform_full_health_check
from backend_api.core.response import success_response, error_response
from loguru import logger
from backend_api.shared.kafka_topics import RAW_TELEMETRY
from backend_api.shared.kafka_client import ResilientKafkaProducer
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
from uuid import UUID
import json
import os
from fastapi import FastAPI, Header

from backend_api.telemetry_ingestor.signed_auth import SignedTelemetryAuthError, SignedTelemetryAuthService

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
TELEMETRY_TOPIC = RAW_TELEMETRY
# --- Global State ---
producer: Optional[ResilientKafkaProducer] = None
telemetry_auth_service = SignedTelemetryAuthService()

def get_kafka_producer():
    global producer
    if producer is None:
        try:
            producer = ResilientKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
            logger.info("Kafka producer initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    return producer

class TelemetryEvent(BaseModel):
    """Canonical event body accepted only after detached-signature verification."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    tenant_id: UUID

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
    custom_shutdown=telemetry_ingestor_shutdown,
    required_dependencies=("kafka",),
)

@app.post("/ingest")
async def ingest_telemetry(
    event: TelemetryEvent,
    x_phantomnet_key_id: str | None = Header(default=None, alias="X-PhantomNet-Key-Id"),
    x_phantomnet_nonce: str | None = Header(default=None, alias="X-PhantomNet-Nonce"),
    x_phantomnet_signed_at: str | None = Header(default=None, alias="X-PhantomNet-Signed-At"),
    x_phantomnet_signature: str | None = Header(default=None, alias="X-PhantomNet-Signature"),
):
    """Authenticate one tenant-bound agent event before durable replay recording and publication."""
    serialized_event = event.model_dump(mode="json")
    try:
        await telemetry_auth_service.verify_and_record(
            event=serialized_event,
            key_id=x_phantomnet_key_id,
            nonce=x_phantomnet_nonce,
            signed_at=x_phantomnet_signed_at,
            signature=x_phantomnet_signature,
        )
    except SignedTelemetryAuthError:
        logger.warning("Rejected signed telemetry submission for the supplied agent identity.")
        return error_response(
            code="SIGNED_TELEMETRY_REJECTED",
            message="Telemetry authentication failed.",
            status_code=403,
        )

    try:
        kafka_producer = get_kafka_producer()
        kafka_producer.send(TELEMETRY_TOPIC, serialized_event)
        logger.info(f"Ingested authenticated telemetry from agent {event.agent_id} for tenant {event.tenant_id}")
        return success_response(data={"status": "ingested"})
    except Exception:
        logger.exception("Authenticated telemetry publication failed.")
        return error_response(code="INGESTION_FAILED", message="Telemetry publication failed.", status_code=500)

@app.get("/health_detailed")
async def health_detailed():
    """
    Returns the comprehensive health status of the Telemetry Ingestor.
    """
    kafka_status = await check_kafka_health()
    full_status = await perform_full_health_check({"kafka_broker": kafka_status})
    return success_response(data=full_status)
