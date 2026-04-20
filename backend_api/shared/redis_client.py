import redis
from loguru import logger
from unittest.mock import MagicMock
from backend_api.core_config import SAFE_MODE

def get_redis_client():
    """
    Initializes and returns a Redis client.
    If SAFE_MODE is True, it returns a mock client immediately.
    Falls back to a mock client if the connection fails.
    """
    if SAFE_MODE:
        logger.warning("SAFE_MODE is ON. Using mock Redis client.")
        mock_client = MagicMock()
        mock_client.ping.return_value = False
        mock_client.pipeline.return_value.execute.return_value = [1, 60]
        return mock_client
        
    try:
        client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        client.ping()
        logger.info("Successfully connected to Redis.")
        return client
    except redis.exceptions.ConnectionError as e:
        logger.warning(f"Could not connect to Redis: {e}. Using mock Redis client.")
        mock_client = MagicMock()
        # Mock common methods to avoid errors
        mock_client.ping.return_value = False
        mock_client.pipeline.return_value.execute.return_value = [1, 60]
        return mock_client

redis_client = get_redis_client()
