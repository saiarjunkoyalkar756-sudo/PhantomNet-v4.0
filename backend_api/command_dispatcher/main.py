import json
import os
import signal
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer
import logging # Import standard logging module
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio
from typing import Optional # For Kafka consumer Optional type hint

from backend_api.shared.logger_config import setup_logging # Import shared logger setup
from backend_api.shared.health_utils import check_kafka_health, check_kafka_consumer_health, perform_full_health_check # Import health_utils

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
COMMAND_TOPIC = 'agent-commands'
GROUP_ID = 'command-dispatcher-group'
APP_PORT = int(os.environ.get('APP_PORT', '8005')) # New port for this service

# --- Setup Logging ---
logger = setup_logging(name="command_dispatcher", level=logging.INFO)

# --- Global Kafka Instances ---
consumer: Optional[KafkaConsumer] = None
processing_task: Optional[asyncio.Task] = None
stop_processing_event = asyncio.Event()

async def consume_and_process_kafka_messages():
    global consumer
    logger.info("Starting Kafka consumer for Command Dispatcher...")

    # It can take a few seconds for the Kafka broker to be ready.
    await asyncio.sleep(15) # Give Redpanda time to start

    try:
        consumer = KafkaConsumer(
            COMMAND_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='latest', # Only get new messages
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info("Kafka consumer initialized successfully.")
    except Exception as e:
        logger.error(f"Could not connect to Kafka: {e}", exc_info=True)
        return

    logger.info("Command Dispatcher started. Polling for commands...")
    try:
        for message in consumer:
            if stop_processing_event.is_set():
                break # Exit loop if shutdown is requested

            try:
                command_data = message.value
                logger.info(f"Received command for agent {command_data.get('target_agent_id')}: {command_data.get('command_type')}", extra=command_data)
                # In a real implementation, this is where the command would be forwarded to the agent
                # For now, we just log it.
                # Example: if command_data.get('command_type') == 'kill_process':
                #              send_to_agent_api(command_data.get('target_agent_id'), command_data)

            except json.JSONDecodeError:
                logger.error(f"Could not decode message: {message.value}")
            except Exception as e:
                logger.error(f"An error occurred during command processing: {e}", exc_info=True)
    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled.")
    except Exception as e:
        logger.critical(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
    finally:
        logger.info("Kafka consumer loop finished.")
        if consumer is not None:
            consumer.close()
            logger.info("Kafka consumer closed.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Command Dispatcher service starting up...")
    global processing_task
    processing_task = asyncio.create_task(consume_and_process_kafka_messages())
    logger.info("Kafka consumer background task initiated.")
    
    yield
    
    # Shutdown logic
    logger.info("Command Dispatcher service shutting down.")
    stop_processing_event.set() # Signal consumer to stop
    if processing_task:
        processing_task.cancel()
        try:
            await processing_task
        except asyncio.CancelledError:
            logger.info("Kafka consumer task cancelled during shutdown.")
    
    logger.info("Command Dispatcher service stopped.")


app = FastAPI(
    title="Command Dispatcher Service",
    description="Consumes agent commands from Kafka and logs them for now (forwards to agents in future).",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """
    Returns the comprehensive health status of the Command Dispatcher service and its Kafka dependencies.
    """
    kafka_status = await check_kafka_health()
    kafka_consumer_status = await check_kafka_consumer_health(COMMAND_TOPIC, GROUP_ID)
    
    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "kafka_consumer": kafka_consumer_status
    })
    
    if full_status["status"] == "healthy":
        logger.info("Command Dispatcher service is healthy.", extra=full_status)
    else:
        logger.warning("Command Dispatcher service is in a degraded state.", extra=full_status)
        
    return full_status