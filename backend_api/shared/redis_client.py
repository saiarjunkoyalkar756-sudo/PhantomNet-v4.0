# backend_api/shared/redis_client.py
"""
Resilient Auto-Reconnecting Redis Client with Exponential Backoff.
Integrates mock fallback during testing or local safe-mode deployments.
"""

import os
import time
import redis
from loguru import logger
from unittest.mock import MagicMock
from backend_api.core_config import SAFE_MODE

class ReconnectingRedisClient:
    """
    Wrapper around redis.Redis that provides auto-reconnect logic
    with exponential backoff on connection failure.
    """
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self._host = host
        self._port = port
        self._db = db
        self._client = None
        self._mock_client = None

    def _get_mock(self) -> MagicMock:
        if not self._mock_client:
            logger.warning("SAFE_MODE is ON, environment is testing, or Redis is down. Using mock Redis client.")
            self._mock_client = MagicMock()
            # Standard return values to keep auth and sessions functional in local tests
            self._mock_client.ping.return_value = False
            self._mock_client.pipeline.return_value.execute.return_value = [1, 60]
            self._mock_client.get.return_value = None
            self._mock_client.setex.return_value = True
        return self._mock_client

    def get_client(self):
        env = os.getenv("ENVIRONMENT", "development").lower()
        if SAFE_MODE or env == "testing":
            return self._get_mock()

        # If client already exists, test if it's still alive
        if self._client:
            try:
                self._client.ping()
                return self._client
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                logger.warning("Redis connection lost. Retrying to connect...")
                self._client = None

        # Reconnect with exponential backoff
        backoff = 0.5
        for attempt in range(5):
            try:
                client = redis.Redis(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    decode_responses=True,
                    socket_connect_timeout=2.0
                )
                client.ping()
                self._client = client
                logger.info("Successfully connected to Redis.")
                return client
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as err:
                logger.warning(f"Redis connection attempt {attempt+1} failed: {err}")
                if attempt == 4:
                    break
                time.sleep(backoff)
                backoff *= 2

        logger.error("Could not connect to Redis after 5 attempts. Falling back to mock client.")
        return self._get_mock()

    def __getattr__(self, name: str):
        # Dynamically forward attributes/calls to the underlying active client (real or mock)
        return getattr(self.get_client(), name)

# Central singleton instance
redis_client = ReconnectingRedisClient()
