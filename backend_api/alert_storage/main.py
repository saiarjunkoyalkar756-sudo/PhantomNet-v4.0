from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.health_utils import check_kafka_health, check_postgres_health, check_kafka_consumer_health, perform_full_health_check
from backend_api.shared.logger_config import setup_logging
from backend_api.core.response import success_response, error_response
from .api import router as alerts_router
from loguru import logger
from uuid import UUID
import json
import os
import asyncio
import psycopg2
import time
from psycopg2 import OperationalError
from kafka import KafkaConsumer
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request, Depends, status

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = 'alerts'
KAFKA_GROUP_ID = 'alert-storage-group'

DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'phantomnet_db')
DB_USER = os.environ.get('DB_USER', 'phantomnet')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001") 

# --- Global State ---
stop_processing_event = asyncio.Event()

def get_db_connection():
    """Establishes a connection to the PostgreSQL database with retry logic."""
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("Database connection successful.")
            return conn
        except OperationalError as e:
            logger.error(f"Database connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

async def consume_and_process_kafka_messages():
    logger.info("Starting Kafka consumer for Alert Storage...")
    await asyncio.sleep(20) # Startup delay

    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            group_id=KAFKA_GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info("Kafka consumer initialized successfully.")
    except Exception as e:
        logger.error(f"Could not connect to Kafka: {e}")
        return

    db_conn = get_db_connection()
    db_cursor = db_conn.cursor()

    INSERT_STMT = """
        INSERT INTO alerts (tenant_id, alert_id, rule_id, rule_name, agent_id, triggered_at, severity, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (alert_id) DO NOTHING;
    """

    try:
        for message in consumer:
            if stop_processing_event.is_set():
                break

            try:
                alert = message.value
                tenant_id_str = alert.get('tenant_id')
                parsed_tenant_id = UUID(tenant_id_str) if tenant_id_str else DEFAULT_TENANT_ID

                db_cursor.execute(INSERT_STMT, (
                    str(parsed_tenant_id),
                    alert.get('alert_id'),
                    alert.get('rule_id'),
                    alert.get('rule_name'),
                    alert.get('agent_id'),
                    alert.get('triggered_at'),
                    alert.get('severity'),
                    alert.get('details')
                ))
                db_conn.commit()
                logger.info(f"Stored alert: {alert.get('alert_id')} for tenant {parsed_tenant_id}")
            except Exception as e:
                logger.error(f"Error processing alert message: {e}")
                db_conn.rollback()

    except asyncio.CancelledError:
        logger.info("Consumer loop cancelled.")
    finally:
        consumer.close()
        db_cursor.close()
        db_conn.close()
        logger.info("Alert Storage backend resources closed.")

async def alert_storage_startup(app: FastAPI):
    app.state.processing_task = asyncio.create_task(consume_and_process_kafka_messages())
    logger.info("Alert Storage: Background consumer task started.")

async def alert_storage_shutdown(app: FastAPI):
    if hasattr(app.state, "processing_task"):
        stop_processing_event.set()
        app.state.processing_task.cancel()
        await asyncio.gather(app.state.processing_task, return_exceptions=True)
        logger.info("Alert Storage: Background consumer task stopped.")

app = create_phantom_service(
    name="Alert Storage Service",
    description="Consumes alerts from Kafka and stores them in PostgreSQL.",
    version="1.0.0",
    custom_startup=alert_storage_startup,
    custom_shutdown=alert_storage_shutdown
)

app.include_router(alerts_router)

@app.get("/health_detailed")
async def health_detailed():
    """
    Returns the comprehensive health status of the Alert Storage service.
    """
    kafka_status = await check_kafka_health()
    kafka_consumer_status = await check_kafka_consumer_health(KAFKA_TOPIC, KAFKA_GROUP_ID)
    postgres_status = await check_postgres_health()
    
    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "kafka_consumer": kafka_consumer_status,
        "postgres_db": postgres_status
    })
    
    return success_response(data=full_status)