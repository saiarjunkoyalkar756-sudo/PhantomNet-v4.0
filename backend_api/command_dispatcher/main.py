from backend_api.shared.service_factory import create_phantom_service
from backend_api.shared.health_utils import check_kafka_health, check_kafka_consumer_health, perform_full_health_check
from backend_api.core.response import success_response, error_response
from loguru import logger
from kafka import KafkaConsumer
import json
import os
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
COMMAND_TOPIC = 'agent-commands'
GROUP_ID = 'command-dispatcher-group'

# --- Global State ---
consumer: Optional[KafkaConsumer] = None

async def consume_and_process_kafka_messages():
    global consumer
    logger.info("Starting Kafka consumer for Command Dispatcher...")
    
    # Delay for Redpanda readiness
    await asyncio.sleep(15)

    try:
        consumer = KafkaConsumer(
            COMMAND_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='latest',
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info("Kafka consumer initialized successfully.")
    except Exception as e:
        logger.error(f"Could not connect to Kafka: {e}")
        return

    logger.info("Command Dispatcher polling for commands...")
    try:
        for message in consumer:
            try:
                command_data = message.value
                logger.info(f"Received command for agent {command_data.get('target_agent_id')}: {command_data.get('command_type')}")
            except Exception as e:
                logger.error(f"Error processing command message: {e}")
    except asyncio.CancelledError:
        logger.info("Kafka consumer loop cancelled.")
    finally:
        if consumer is not None:
            consumer.close()
            logger.info("Kafka consumer closed.")

async def command_dispatcher_startup(app: FastAPI):
    """
    Handles startup events for the Command Dispatcher.
    """
    app.state.processing_task = asyncio.create_task(consume_and_process_kafka_messages())
    logger.info("Command Dispatcher: Background consumer task started.")

async def command_dispatcher_shutdown(app: FastAPI):
    """
    Handles shutdown events for the Command Dispatcher.
    """
    if hasattr(app.state, "processing_task"):
        app.state.processing_task.cancel()
        await asyncio.gather(app.state.processing_task, return_exceptions=True)
    logger.info("Command Dispatcher: Background consumer task stopped.")

app = create_phantom_service(
    name="Command Dispatcher Service",
    description="Consumes agent commands from Kafka and manages their lifecycle.",
    version="1.0.0",
    custom_startup=command_dispatcher_startup,
    custom_shutdown=command_dispatcher_shutdown
)

@app.get("/health_detailed")
async def health_detailed():
    """
    Returns the comprehensive health status of the Command Dispatcher.
    """
    kafka_status = await check_kafka_health()
    kafka_consumer_status = await check_kafka_consumer_health(COMMAND_TOPIC, GROUP_ID)
    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "kafka_consumer": kafka_consumer_status
    })
    return success_response(data=full_status)