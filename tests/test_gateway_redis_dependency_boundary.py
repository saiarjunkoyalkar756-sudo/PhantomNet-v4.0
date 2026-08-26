"""Fail-closed request-security contracts for the self-hosted gateway Redis dependency."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError

from backend_api.gateway_service import main as gateway_main
from backend_api.shared import redis_client as redis_module


def test_non_safe_mode_redis_outage_refuses_mock_fallback(monkeypatch):
    monkeypatch.setattr(redis_module, "SAFE_MODE", False)
    monkeypatch.setenv("PHANTOMNET_ENVIRONMENT", "staging")

    unavailable_client = MagicMock()
    unavailable_client.ping.side_effect = ConnectionError("unavailable")
    with patch.object(redis_module.redis.Redis, "from_url", return_value=unavailable_client):
        client = redis_module.ReconnectingRedisClient(
            redis_url="redis://unavailable.example:6379/0",
            max_attempts=1,
        )
        with pytest.raises(redis_module.RedisUnavailable, match="safe mode is disabled"):
            client.get_client()


def test_test_environment_retains_local_redis_mock(monkeypatch):
    monkeypatch.setattr(redis_module, "SAFE_MODE", False)
    monkeypatch.setenv("PHANTOMNET_ENVIRONMENT", "testing")

    client = redis_module.ReconnectingRedisClient(max_attempts=1)

    assert client.get_client().pipeline().execute() == [1, 60]


def test_gateway_refuses_request_when_rate_limit_dependency_is_unavailable():
    database_session = MagicMock()
    database_session.query.return_value.filter.return_value.first.return_value = None

    with patch.object(gateway_main, "SessionLocal", return_value=database_session), patch.object(
        gateway_main.redis_client,
        "pipeline",
        side_effect=redis_module.RedisUnavailable("Redis is unavailable while safe mode is disabled."),
    ):
        response = TestClient(gateway_main.app).get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Request security controls are temporarily unavailable."}
