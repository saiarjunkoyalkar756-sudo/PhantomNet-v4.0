# backend_api/shared/health.py
import asyncio
from typing import Dict, Any
from loguru import logger
import redis
import psycopg2
from kafka import KafkaConsumer

from backend_api.shared.settings import settings
from backend_api.core_config import SAFE_MODE

async def check_db_health() -> Dict[str, Any]:
    """Checks connection to PostgreSQL database."""
    if SAFE_MODE:
        return {"status": "healthy", "details": "Safe mode active (mock database)."}
    try:
        # Simple blocking call in executor
        loop = asyncio.get_event_loop()
        def _connect():
            # Parse DB connection parameters from settings.DATABASE_URL
            # Simple fallback check
            conn = psycopg2.connect(
                dbname=settings.DATABASE_URL.split("/")[-1].split("?")[0],
                user=settings.DATABASE_URL.split("://")[1].split(":")[0],
                password=settings.DATABASE_URL.split(":")[2].split("@")[0],
                host=settings.DATABASE_URL.split("@")[1].split(":")[0],
                port=int(settings.DATABASE_URL.split("@")[1].split(":")[1].split("/")[0])
            )
            conn.cursor().execute("SELECT 1;")
            conn.close()
        await loop.run_in_executor(None, _connect)
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

async def check_kafka_health() -> Dict[str, Any]:
    """Checks connection to Kafka bootstrap servers."""
    if SAFE_MODE:
        return {"status": "healthy", "details": "Safe mode active (mock Kafka)."}
    try:
        loop = asyncio.get_event_loop()
        def _check():
            consumer = KafkaConsumer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                request_timeout_ms=2000
            )
            consumer.topics()
            consumer.close()
        await loop.run_in_executor(None, _check)
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Kafka health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

async def check_redis_health() -> Dict[str, Any]:
    """Checks connection to Redis cache."""
    if SAFE_MODE:
        return {"status": "healthy", "details": "Safe mode active (mock Redis)."}
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            socket_timeout=2
        )
        r.ping()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

async def run_standard_health_check() -> Dict[str, Any]:
    """
    Standard health check execution for all microservices.
    Runs database, Kafka, and Redis connectivity audits concurrently.
    """
    db_task = asyncio.create_task(check_db_health())
    kafka_task = asyncio.create_task(check_kafka_health())
    redis_task = asyncio.create_task(check_redis_health())
    
    db_res, kafka_res, redis_res = await asyncio.gather(db_task, kafka_task, redis_task)
    
    is_healthy = (
        db_res["status"] == "healthy" and 
        kafka_res["status"] == "healthy" and 
        redis_res["status"] == "healthy"
    )
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "components": {
            "database": db_res,
            "kafka": kafka_res,
            "redis": redis_res
        }
    }
