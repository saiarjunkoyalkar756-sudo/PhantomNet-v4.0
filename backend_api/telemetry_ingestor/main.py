from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from pydantic import BaseModel
from typing import Dict, Any
from uuid import UUID # Import UUID for tenant_id
import logging # Import standard logging module
from backend_api.shared.logger_config import setup_logging # Import shared logger setup
from backend_api.shared.health_utils import check_kafka_health, perform_full_health_check # Import health_utils

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = 'redpanda:29092'
TELEMETRY_TOPIC = 'telemetry-events'

# Default tenant ID for events if not provided by the agent
# In a real system, this would be derived from agent registration or JWT token
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")

# --- Setup Logging ---
logger = setup_logging(name="telemetry_ingestor", level=logging.INFO)

# --- Kafka Producer Setup ---
# Using a lambda to delay producer connection until it's first used.
producer = None
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
            logger.error(f"Failed to initialize Kafka producer: {e}", exc_info=True)
            raise # Re-raise to prevent app from starting without producer
    return producer

# --- FastAPI Application ---
app = FastAPI(
    title="Telemetry Ingestor",
    description="Receives telemetry data from PhantomNet agents and publishes it to the event bus.",
    version="1.0.0"
)

class TelemetryEvent(BaseModel):
    agent_id: str
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    tenant_id: UUID = DEFAULT_TENANT_ID # Assign default if not provided

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Telemetry Ingestor shutting down.")
    if producer is not None:
        producer.close()
        logger.info("Kafka producer closed.")

@app.post("/ingest")
async def ingest_telemetry(event: TelemetryEvent):
    """
    Ingest a single telemetry event from an agent.
    """
    try:
        kafka_producer = get_kafka_producer()
        kafka_producer.send(TELEMETRY_TOPIC, event.dict())
        logger.info(f"Ingested event from agent {event.agent_id} for tenant {event.tenant_id}", extra={"agent_id": event.agent_id, "tenant_id": str(event.tenant_id), "event_type": event.event_type})
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error ingesting telemetry event: {e}", exc_info=True, extra={"event": event.dict()})
        raise HTTPException(status_code=500, detail="Internal Server Error") # Raise HTTPException for client visibility

@app.get("/health")
async def health_check():
    kafka_status = await check_kafka_health()
    full_status = await perform_full_health_check({"kafka_broker": kafka_status})
    return full_status

