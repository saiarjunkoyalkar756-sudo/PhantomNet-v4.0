from fastapi import APIRouter, Depends
import logging
from backend_api.shared.health_utils import check_kafka_health, check_postgres_health, perform_full_health_check
from backend_api.shared.logger_config import setup_logging

logger = setup_logging(name="gateway_health_router", level="INFO")

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)

@router.get("/")
async def get_health_status():
    """
    Returns the comprehensive health status of the Gateway service and its dependencies.
    Checks Kafka, PostgreSQL, and Redis (placeholder for Redis check).
    """
    kafka_status = await check_kafka_health()
    postgres_status = await check_postgres_health()
    
    # Placeholder for Redis health check (needs a dedicated function in health_utils)
    redis_status = {"redis_status": "healthy", "message": "Redis health check not yet implemented."}

    full_status = await perform_full_health_check({
        "kafka_broker": kafka_status,
        "postgres_db": postgres_status,
        "redis_cache": redis_status
    })
    
    # Log overall status
    if full_status["status"] == "healthy":
        logger.info("Gateway service is healthy.", extra=full_status)
    else:
        logger.warning("Gateway service is in a degraded state.", extra=full_status)
        
    return full_status
