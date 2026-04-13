import asyncio
import os
import logging
import json
from typing import Dict, Any
from kafka import KafkaAdminClient, KafkaConsumer
# import psycopg2
# from psycopg2 import OperationalError

logger = logging.getLogger("phantomnet_shared.health_utils")

KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'phantomnet_db')
DB_USER = os.environ.get('DB_USER', 'phantomnet')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

async def check_kafka_health() -> Dict[str, Any]:
    """Checks Kafka connectivity and broker availability."""
    health_status = {"kafka_status": "unhealthy", "error": None}
    try:
        # Try to connect KafkaAdminClient
        admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                        client_id='health_check_admin')
        # List topics as a basic check for broker availability
        admin_client.list_topics()
        admin_client.close()
        health_status["kafka_status"] = "healthy"
    except Exception as e:
        health_status["error"] = str(e)
        logger.error(f"Kafka health check failed: {e}", exc_info=True)
    return health_status

async def check_kafka_consumer_health(topic: str, group_id: str) -> Dict[str, Any]:
    """Checks if a Kafka consumer can connect and fetch metadata for a specific topic."""
    health_status = {"kafka_consumer_status": "unhealthy", "error": None}
    consumer = None
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            client_id=f'{group_id}_health_check',
            auto_offset_reset='latest', # Don't process old messages
            consumer_timeout_ms=1000 # Wait for 1 second for messages
        )
        # Try to get topics, which forces a connection
        consumer.topics() 
        health_status["kafka_consumer_status"] = "healthy"
    except Exception as e:
        health_status["error"] = str(e)
        logger.error(f"Kafka consumer health check failed for topic {topic}: {e}", exc_info=True)
    finally:
        if consumer:
            consumer.close()
    return health_status


async def check_postgres_health() -> Dict[str, Any]:
    """
    Mocks PostgreSQL database connectivity check.
    Always reports unhealthy because psycopg2 is not installed.
    """
    logger.warning("PostgreSQL health check is mocked as psycopg2 driver is not installed.")
    return {"postgres_status": "unhealthy", "error": "psycopg2 driver not installed. PostgreSQL check disabled."}

async def perform_full_health_check(checks: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs a set of health checks concurrently.
    `checks` is a dictionary where keys are check names and values are awaitable functions.
    Example: {"kafka": check_kafka_health(), "postgres": check_postgres_health()}
    """
    results = await asyncio.gather(*checks.values(), return_exceptions=True)
    
    full_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    for i, (check_name, _) in enumerate(checks.items()):
        result = results[i]
        if isinstance(result, Exception):
            full_status["status"] = "degraded"
            full_status["services"][check_name] = {"status": "error", "error": str(result)}
            logger.error(f"Health check '{check_name}' failed with an exception: {result}", exc_info=True)
        else:
            full_status["services"][check_name] = result
            if "unhealthy" in json.dumps(result): # Simple check for "unhealthy" string in any part of the result
                 full_status["status"] = "degraded"
            
    return full_status
