# backend_api/threat_intelligence_service/cache.py

import os
import json
import redis
import asyncio # Import asyncio
from typing import Optional, Any
from datetime import datetime, timedelta

from shared.logger_config import logger

logger = logger

# Cache configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL_SECONDS = int(os.getenv("THREAT_INTEL_CACHE_TTL", 3600)) # Default 1 hour

class RedisCache:
    """
    Implements a Redis-based cache for threat intelligence results.
    """
    def __init__(self):
        try:
            self.client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
            self.client.ping()
            logger.info(f"Connected to Redis cache at {REDIS_HOST}:{REDIS_PORT}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Caching will be disabled. Error: {e}")
            self.client = None # Disable caching if connection fails

    def get(self, key: str) -> Optional[Any]:
        """Retrieves an item from the cache."""
        if not self.client:
            return None
        try:
            data = self.client.get(key)
            if data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(data)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from Redis cache for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> bool:
        """Stores an item in the cache with a TTL."""
        if not self.client:
            return False
        try:
            self.client.setex(key, ttl, json.dumps(value))
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error setting to Redis cache for key {key}: {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """Invalidates a specific key in the cache."""
        if not self.client:
            return False
        try:
            self.client.delete(key)
            logger.debug(f"Cache invalidated for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error invalidating Redis cache for key {key}: {e}")
            return False

    async def ping(self):
        """Pings the Redis server to check the connection."""
        if not self.client:
            raise redis.exceptions.ConnectionError("Redis client not initialized.")
        # The underlying redis-py client's ping is synchronous,
        # but we run it in an executor to be non-blocking in an async context.
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.client.ping)


# Global cache instance
threat_intel_cache = RedisCache()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running RedisCache example...")
    
    # Ensure a local Redis instance is running or configure REDIS_HOST/REDIS_PORT
    
    cache = RedisCache()
    
    test_key = "test_indicator_123"
    test_value = {"indicator": "1.1.1.1", "threat": True}

    # Test set
    cache.set(test_key, test_value, ttl=5)
    logger.info(f"Set '{test_key}' to cache.")

    # Test get (hit)
    retrieved_value = cache.get(test_key)
    logger.info(f"Retrieved '{test_key}' from cache: {retrieved_value}")
    assert retrieved_value == test_value

    # Test get (miss after TTL)
    logger.info("Waiting for TTL to expire (5 seconds)...")
    asyncio.run(asyncio.sleep(5)) # Use asyncio.sleep since we're in an async context
    retrieved_value_expired = cache.get(test_key)
    logger.info(f"Retrieved '{test_key}' after TTL: {retrieved_value_expired}")
    assert retrieved_value_expired is None

    # Test invalidate
    cache.set(test_key, test_value)
    logger.info(f"Set '{test_key}' again for invalidation test.")
    cache.invalidate(test_key)
    retrieved_value_invalidated = cache.get(test_key)
    logger.info(f"Retrieved '{test_key}' after invalidation: {retrieved_value_invalidated}")
    assert retrieved_value_invalidated is None
    
    logger.info("RedisCache example completed.")
