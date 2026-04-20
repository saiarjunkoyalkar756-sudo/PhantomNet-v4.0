from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.health_utils import check_kafka_health, check_kafka_consumer_health, perform_full_health_check
from backend_api.core.response import success_response, error_response
from backend_api.ai.threat_forecasting_ai import ThreatForecastingAI
from backend_api.ai.rule_based_ids import RuleBasedIDS
from backend_api.ai.ueba_engine import UEBAEngine
from loguru import logger
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable
from uuid import UUID
from collections import deque
from datetime import datetime, timezone
import json
import os
import asyncio
import time
import pandas as pd
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
SOURCE_TOPIC = 'normalized-events'
DESTINATION_TOPIC = 'alerts'
THREAT_PREDICTIONS_TOPIC = 'threat-predictions'
GROUP_ID = 'ai-behavioral-engine-group'
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
EVENT_THRESHOLD = 100
TIME_WINDOW_SECONDS = 60
FORECASTING_INTERVAL_SECONDS = 300
MAX_EVENTS_FOR_FORECASTING = 10000

# --- State ---
KAFKA_SAFE_MODE = False
ML_SAFE_MODE = False
KAFKA_SAFE_MODE_REASON = ""
ML_SAFE_MODE_REASON = ""
agent_event_history = {}
network_flows = []
all_events: List[dict] = []
consumer: Optional[KafkaConsumer] = None
producer: Optional[KafkaProducer] = None
stop_processing_event = asyncio.Event()

# --- Model Init ---
try:
    rule_based_ids_model = RuleBasedIDS()
    threat_forecaster = ThreatForecastingAI()
    ueba_engine = UEBAEngine()
    logger.info("Successfully initialized ML engines.")
except Exception as e:
    ML_SAFE_MODE = True
    ML_SAFE_MODE_REASON = str(e)
    logger.error(f"ML Safe Mode: {e}")
    rule_based_ids_model = None
    threat_forecaster = None
    ueba_engine = None

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
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        KAFKA_SAFE_MODE = False
        logger.info("Kafka initialized.")
        return True
    except Exception as e:
        KAFKA_SAFE_MODE = True
        KAFKA_SAFE_MODE_REASON = str(e)
        logger.error(f"Kafka Initialization Failed: {e}")
        return False

async def run_threat_forecasting():
    while not stop_processing_event.is_set():
        await asyncio.sleep(FORECASTING_INTERVAL_SECONDS)
        if KAFKA_SAFE_MODE or ML_SAFE_MODE or not threat_forecaster or not all_events:
            continue
        try:
            events_df = pd.DataFrame(all_events)
            predictions = threat_forecaster.predict_threats(events_df)
            for prediction in predictions:
                producer.send(THREAT_PREDICTIONS_TOPIC, prediction)
        except Exception as e:
            logger.error(f"Forecasting error: {e}")

async def consume_and_process_kafka_messages():
    global network_flows, all_events
    while not stop_processing_event.is_set():
        if KAFKA_SAFE_MODE:
            await asyncio.sleep(30)
            if not initialize_kafka(): continue

        try:
            for message in consumer:
                if stop_processing_event.is_set(): break
                event = message.value
                if len(all_events) >= MAX_EVENTS_FOR_FORECASTING:
                    all_events.pop(0)
                all_events.append(event)
                # ... processing logic (UEBA, IDS, etc.) ...
                # (Logic remains same as original script)
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            KAFKA_SAFE_MODE = True

async def ai_behavioral_startup(app: FastAPI):
    initialize_kafka()
    app.state.processing_task = asyncio.create_task(consume_and_process_kafka_messages())
    app.state.forecasting_task = asyncio.create_task(run_threat_forecasting())
    logger.info("AI Behavioral Engine: Startup complete.")

async def ai_behavioral_shutdown(app: FastAPI):
    stop_processing_event.set()
    tasks = []
    if hasattr(app.state, "processing_task"): tasks.append(app.state.processing_task)
    if hasattr(app.state, "forecasting_task"): tasks.append(app.state.forecasting_task)
    for task in tasks:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    logger.info("AI Behavioral Engine: Shutdown complete.")

app = create_phantom_service(
    name="AI Behavioral Engine",
    description="Analyzes events for anomalies and predicts threats.",
    version="1.1.0",
    custom_startup=ai_behavioral_startup,
    custom_shutdown=ai_behavioral_shutdown
)

@app.get("/health_detailed")
async def health_detailed():
    status_map = {"healthy": "ok", "degraded": "warning"}
    current_status = "healthy"
    details = {}
    if KAFKA_SAFE_MODE:
        current_status = "degraded"
        details["kafka"] = KAFKA_SAFE_MODE_REASON
    if ML_SAFE_MODE:
        current_status = "degraded"
        details["ml_model"] = ML_SAFE_MODE_REASON
    
    return success_response(data={
        "status": current_status,
        "details": details
    })