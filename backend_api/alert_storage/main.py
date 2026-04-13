import json
import os
import signal
import time
import psycopg2
from psycopg2 import OperationalError
from kafka import KafkaConsumer
from uuid import UUID # Import UUID
import logging # Import standard logging module
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio
from typing import Optional # For Kafka consumer/producer Optional type hint

from backend_api.shared.logger_config import setup_logging # Import shared logger setup
from backend_api.shared.health_utils import check_kafka_health, check_postgres_health, check_kafka_consumer_health, perform_full_health_check # Import health_utils

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
KAFKA_TOPIC = 'alerts'
KAFKA_GROUP_ID = 'alert-storage-group'
APP_PORT = int(os.environ.get('APP_PORT', '8004')) # New port for this service

DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'phantomnet_db')
DB_USER = os.environ.get('DB_USER', 'phantomnet')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# Default tenant ID for alerts if not specified in the message
# In a real system, this would come from context provided by the ingestor/agent
DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001") 

# --- Setup Logging ---
logger = setup_logging(name="alert_storage", level=logging.INFO)

# --- Global Kafka and DB Instances ---
consumer: Optional[KafkaConsumer] = None
db_conn: Optional[psycopg2.extensions.connection] = None
db_cursor: Optional[psycopg2.extensions.cursor] = None
processing_task: Optional[asyncio.Task] = None
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
    global consumer, db_conn, db_cursor
    logger.info("Starting Kafka consumer for Alert Storage...")

    # It can take a few seconds for Kafka to be ready
    await asyncio.sleep(20) # Give Redpanda and Postgres time to start

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
        logger.error(f"Could not connect to Kafka: {e}", exc_info=True)
        return

    db_conn = get_db_connection()
    db_cursor = db_conn.cursor()

    INSERT_STMT = """
        INSERT INTO alerts (tenant_id, alert_id, rule_id, rule_name, agent_id, triggered_at, severity, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (alert_id) DO NOTHING;
    """

    logger.info("Alert Storage service started. Polling for alert messages...")
    try:
        for message in consumer:
            if stop_processing_event.is_set():
                break # Exit loop if shutdown is requested

            try:
                alert = message.value
                logger.debug(f"Received alert: {alert.get('alert_id')}")

                # Extract tenant_id from alert, or use default
                tenant_id_str = alert.get('tenant_id')
                parsed_tenant_id = UUID(tenant_id_str) if tenant_id_str else DEFAULT_TENANT_ID

                db_cursor.execute(INSERT_STMT, (
                    str(parsed_tenant_id), # Ensure UUID is passed as string
                    alert.get('alert_id'),
                    alert.get('rule_id'),
                    alert.get('rule_name'),
                    alert.get('agent_id'),
                    alert.get('triggered_at'),
                    alert.get('severity'),
                    alert.get('details')
                ))
                db_conn.commit()
                logger.info(f"Successfully stored alert: {alert.get('alert_id')} for tenant {str(parsed_tenant_id)}", extra=alert)

            except (psycopg2.Error, json.JSONDecodeError) as e:
                logger.error(f"An error occurred while processing message: {e}", exc_info=True, extra={"message_value": message.value})
                db_conn.rollback() # Rollback the failed transaction
            except Exception as e:
                logger.critical(f"A critical error occurred: {e}", exc_info=True, extra={"message_value": message.value})
                # Attempt graceful shutdown here only if critical and unrecoverable
                stop_processing_event.set() # Signal main loop to stop

    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled.")
    except Exception as e:
        logger.critical(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
    finally:
        logger.info("Kafka consumer loop finished.")
        if consumer is not None:
            consumer.close()
            logger.info("Kafka consumer closed.")
        if db_cursor is not None:
            db_cursor.close()
        if db_conn is not None:
            db_conn.close()
            logger.info("Database connection closed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Alert Storage service starting up...")
    global processing_task
    processing_task = asyncio.create_task(consume_and_process_kafka_messages())
    logger.info("Kafka consumer background task initiated.")
    
    yield
    
    # Shutdown logic
    logger.info("Alert Storage service shutting down.")
    stop_processing_event.set() # Signal consumer to stop
    if processing_task:
        processing_task.cancel()
        try:
            await processing_task
        except asyncio.CancelledError:
            logger.info("Kafka consumer task cancelled during shutdown.")
    
    logger.info("Alert Storage service stopped.")


from .api import router as alerts_router
...

app = FastAPI(
    title="Alert Storage Service",
    description="Consumes alerts from Kafka and stores them in PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(alerts_router)

@app.get("/health")
...
async def health_check():
    """
    Returns the comprehensive health status of the Alert Storage service and its dependencies (Kafka, PostgreSQL).
    """
    kafka_status = await check_kafka_health()
    kafka_consumer_status = await check_kafka_consumer_health(KAFKA_TOPIC, KAFKA_GROUP_ID)
    postgres_status = await check_postgres_health()
    
    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "kafka_consumer": kafka_consumer_status,
        "postgres_db": postgres_status
    })
    
    if full_status["status"] == "healthy":
        logger.info("Alert Storage service is healthy.", extra=full_status)
    else:
        logger.warning("Alert Storage service is in a degraded state.", extra=full_status)
        
    return full_status