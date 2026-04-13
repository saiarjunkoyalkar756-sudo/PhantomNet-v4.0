import json
import os
import signal
import time
from collections import deque
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from uuid import UUID
import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio
from typing import Optional, List

from backend_api.shared.logger_config import setup_logging
from backend_api.shared.health_utils import check_kafka_health, check_kafka_consumer_health, perform_full_health_check
import pandas as pd

from backend_api.ai.threat_forecasting_ai import ThreatForecastingAI

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
SOURCE_TOPIC = 'normalized-events'
DESTINATION_TOPIC = 'alerts'
THREAT_PREDICTIONS_TOPIC = 'threat-predictions'
GROUP_ID = 'ai-behavioral-engine-group'
APP_PORT = int(os.environ.get('APP_PORT', '8003'))
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
EVENT_THRESHOLD = 100
TIME_WINDOW_SECONDS = 60
FORECASTING_INTERVAL_SECONDS = 300 # Run forecasting every 5 minutes
MAX_EVENTS_FOR_FORECASTING = 10000 # Max events to keep in memory for forecasting

# --- SAFE MODE Flags ---
KAFKA_SAFE_MODE = False
ML_SAFE_MODE = False
KAFKA_SAFE_MODE_REASON = ""
ML_SAFE_MODE_REASON = ""

# --- In-Memory State ---
agent_event_history = {}
network_flows = []
all_events: List[dict] = []


# --- Setup Logging ---
logger = setup_logging(name="ai_behavioral_engine", level=logging.INFO)

# --- ML Model Loading ---
try:
    rule_based_ids_model = RuleBasedIDS()
    threat_forecaster = ThreatForecastingAI()
    logger.info("Successfully initialized RuleBasedIDS and ThreatForecastingAI.")
except ImportError as e:
    ML_SAFE_MODE = True
    ML_SAFE_MODE_REASON = f"TensorFlow/Keras not installed or model files missing: {e}"
    logger.critical(f"!!! ML SAFE MODE ACTIVATED: {ML_SAFE_MODE_REASON} !!!")
    logger.critical("!!! AI-based network anomaly detection will be disabled. !!!")
    network_ids_model = None
    threat_forecaster = None
except Exception as e:
    ML_SAFE_MODE = True
    ML_SAFE_MODE_REASON = f"An unexpected error occurred while loading the ML model: {e}"
    logger.critical(f"!!! ML SAFE MODE ACTIVATED: {ML_SAFE_MODE_REASON} !!!", exc_info=True)
    network_ids_model = None
    threat_forecaster = None


# --- Global Kafka Instances ---
consumer: Optional[KafkaConsumer] = None
producer: Optional[KafkaProducer] = None
processing_task: Optional[asyncio.Task] = None
forecasting_task: Optional[asyncio.Task] = None
stop_processing_event = asyncio.Event()

def initialize_kafka():
    global consumer, producer, KAFKA_SAFE_MODE, KAFKA_SAFE_MODE_REASON
    try:
        if consumer: consumer.close()
        if producer: producer.close()

        consumer = KafkaConsumer(
            SOURCE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=1000
        )
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info("Kafka consumer and producer initialized successfully.")
        KAFKA_SAFE_MODE = False
        return True
    except NoBrokersAvailable:
        KAFKA_SAFE_MODE = True
        KAFKA_SAFE_MODE_REASON = "Could not connect to Kafka: No brokers available."
        logger.error(KAFKA_SAFE_MODE_REASON)
        return False
    except Exception as e:
        KAFKA_SAFE_MODE = True
        KAFKA_SAFE_MODE_REASON = f"An unexpected error occurred during Kafka initialization: {e}"
        logger.error(KAFKA_SAFE_MODE_REASON, exc_info=True)
        return False

# --- Alert Generation ---
def generate_alert(tenant_id: UUID, agent_id: str, event_count: int, timeframe: int):
    """Creates a structured alert message."""
    return {
        "alert_id": f"alert-{int(time.time() * 1000)}",
        "tenant_id": str(tenant_id),
        "rule_id": "rule_high_event_frequency_v1",
        "rule_name": "High Frequency Event Anomaly",
        "agent_id": agent_id,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "severity": "medium",
        "details": f"Agent {agent_id} generated {event_count} events in the last {timeframe} seconds, exceeding the threshold of {EVENT_THRESHOLD}."
    }

def generate_network_alert(tenant_id: UUID, agent_id: str, anomaly: dict):
    """Creates a structured network alert message."""
    return {
        "alert_id": f"alert-{int(time.time() * 1000)}",
        "tenant_id": str(tenant_id),
        "rule_id": f"rule_network_anomaly_{anomaly['type'].lower().replace(' ', '_')}",
        "rule_name": f"Network Anomaly - {anomaly['type']}",
        "agent_id": agent_id,
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "severity": "high",
        "details": anomaly['description']
    }

async def run_threat_forecasting():
    """Periodically runs threat forecasting."""
    while not stop_processing_event.is_set():
        await asyncio.sleep(FORECASTING_INTERVAL_SECONDS)
        if KAFKA_SAFE_MODE or ML_SAFE_MODE or not threat_forecaster:
            logger.warning("Threat forecasting skipped due to SAFE MODE or missing model.")
            continue
            
        logger.info(f"Running threat forecasting with {len(all_events)} events.")
        if not all_events:
            continue
            
        try:
            events_df = pd.DataFrame(all_events)
            predictions = threat_forecaster.predict_threats(events_df)
            for prediction in predictions:
                logger.info(f"THREAT PREDICTION: {prediction['description']}", extra=prediction)
                producer.send(THREAT_PREDICTIONS_TOPIC, prediction)
        except Exception as e:
            logger.error(f"Error during threat forecasting: {e}", exc_info=True)


async def consume_and_process_kafka_messages():
    global network_flows, all_events
    
    while not stop_processing_event.is_set():
        if KAFKA_SAFE_MODE:
            logger.warning("Kafka is in SAFE MODE. Retrying connection in 30 seconds.")
            await asyncio.sleep(30)
            if not initialize_kafka():
                continue

        logger.info("AI Engine started. Polling for messages...")
        try:
            for message in consumer:
                if stop_processing_event.is_set():
                    break
                
                # Process message
                try:
                    event = message.value
                    
                    # Add to master list for forecasting, capped at MAX_EVENTS_FOR_FORECASTING
                    if len(all_events) >= MAX_EVENTS_FOR_FORECASTING:
                        all_events.pop(0) # Remove the oldest event
                    all_events.append(event)
                    
                    agent_id = event.get('agent_id')
                    tenant_id = UUID(event.get('tenant_id', str(DEFAULT_TENANT_ID)))
                    
                    if not ML_SAFE_MODE and event.get("type") == "packet_metadata":
                        network_flows.append(event.get("data"))
                        if len(network_flows) >= 100:
                            df = pd.DataFrame(network_flows)
                            anomalies = rule_based_ids_model.detect_anomalies(df)
                            for anomaly in anomalies:
                                alert = generate_network_alert(tenant_id, agent_id, anomaly)
                                producer.send(DESTINATION_TOPIC, alert)
                            network_flows = []
                    
                    if not agent_id: continue
                    
                    current_time = time.time()
                    if agent_id not in agent_event_history:
                        agent_event_history[agent_id] = deque()
                    history = agent_event_history[agent_id]
                    history.append(current_time)
                    
                    while history and history[0] < current_time - TIME_WINDOW_SECONDS:
                        history.popleft()
                        
                    if len(history) > EVENT_THRESHOLD:
                        alert = generate_alert(tenant_id, agent_id, len(history), TIME_WINDOW_SECONDS)
                        logger.warning(f"ALERT: {alert['details']}", extra=alert)
                        producer.send(DESTINATION_TOPIC, alert)
                        history.clear()
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)

        except NoBrokersAvailable:
            logger.error("Lost connection to Kafka. Entering SAFE MODE.")
            KAFKA_SAFE_MODE = True
        except Exception as e:
            logger.error(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
            KAFKA_SAFE_MODE = True # Assume Kafka is down
            await asyncio.sleep(10) # Wait before retrying connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("AI Behavioral Engine service starting up...")
    initialize_kafka() # Initial connection attempt
    global processing_task, forecasting_task
    processing_task = asyncio.create_task(consume_and_process_kafka_messages())
    forecasting_task = asyncio.create_task(run_threat_forecasting())
    logger.info("Kafka consumer and threat forecasting background tasks initiated.")
    yield
    # Shutdown logic
    logger.info("AI Behavioral Engine service shutting down.")
    stop_processing_event.set()
    
    tasks = [processing_task, forecasting_task]
    for task in tasks:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Task cancelled during shutdown.")
    
    logger.info("AI Behavioral Engine service stopped.")

app = FastAPI(
    title="AI Behavioral Engine",
    description="Analyzes normalized events for behavioral anomalies, generates alerts, and predicts future threats.",
    version="1.1.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """
    Returns the health status of the AI Behavioral Engine service.
    """
    status = "healthy"
    details = {}
    if KAFKA_SAFE_MODE:
        status = "degraded"
        details["kafka"] = KAFKA_SAFE_MODE_REASON
    if ML_SAFE_MODE:
        status = "degraded"
        details["ml_model"] = ML_SAFE_MODE_REASON
    
    if status == "healthy":
        return {"status": "ok", "message": "AI Behavioral Engine is healthy"}
    else:
        raise HTTPException(
            status_code=503,
            detail={"status": status, "message": "Service is running in a degraded state.", "details": details}
        )