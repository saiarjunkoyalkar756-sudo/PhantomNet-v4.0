"""Redis client boundary with safe-mode mocks and non-safe-mode fail-closed behavior."""
from __future__ import annotations

import os
import time
from unittest.mock import MagicMock

import redis
from loguru import logger

from backend_api.core_config import SAFE_MODE


class RedisUnavailable(RuntimeError):
    """Raised when a non-safe-mode service cannot reach its configured Redis dependency."""


def _runtime_environment() -> str:
    """Return the deployment environment without exposing configuration values."""
    return os.getenv("PHANTOMNET_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")).strip().lower()


class ReconnectingRedisClient:
    """Reconnect to configured Redis, allowing mocks only for safe or test execution."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        *,
        redis_url: str | None = None,
        max_attempts: int = 5,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._redis_url = redis_url if redis_url is not None else os.getenv("REDIS_URL")
        self._max_attempts = max_attempts
        self._client = None
        self._mock_client = None

    def _get_mock(self) -> MagicMock:
        if not self._mock_client:
            logger.warning("Using an in-memory Redis mock only because safe mode or test mode is active.")
            self._mock_client = MagicMock()
            self._mock_client.ping.return_value = False
            self._mock_client.pipeline.return_value.execute.return_value = [1, 60]
            self._mock_client.get.return_value = None
            self._mock_client.setex.return_value = True
        return self._mock_client

    def _new_client(self):
        connection_options = {
            "decode_responses": True,
            "socket_connect_timeout": 2.0,
            "socket_timeout": 2.0,
        }
        if self._redis_url:
            return redis.Redis.from_url(self._redis_url, **connection_options)
        return redis.Redis(host=self._host, port=self._port, db=self._db, **connection_options)

    def get_client(self):
        if SAFE_MODE or _runtime_environment() in {"test", "testing"}:
            return self._get_mock()

        if self._client:
            try:
                self._client.ping()
                return self._client
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                logger.warning("Redis connection lost; reconnecting before allowing another request.")
                self._client = None

        backoff = 0.5
        for attempt in range(self._max_attempts):
            try:
                client = self._new_client()
                client.ping()
                self._client = client
                logger.info("Connected to configured Redis dependency.")
                return client
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                logger.warning("Redis connection attempt {} failed.", attempt + 1)
                if attempt + 1 < self._max_attempts:
                    time.sleep(backoff)
                    backoff *= 2

        logger.error("Redis is unavailable while safe mode is disabled; refusing mock fallback.")
        raise RedisUnavailable("Redis is unavailable while safe mode is disabled.")

    def __getattr__(self, name: str):
        return getattr(self.get_client(), name)


redis_client = ReconnectingRedisClient()
