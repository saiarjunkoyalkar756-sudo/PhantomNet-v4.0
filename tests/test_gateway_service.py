# tests/test_gateway_service.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend_api.gateway_service.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_db_session():
    with patch("backend_api.gateway_service.main.SessionLocal") as mock_session_cls:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session_cls.return_value = mock_session
        yield mock_session

def test_cors_headers():

    """Verify CORS headers are present on options request."""
    response = client.options("/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] in ["*", "http://localhost:3000"]

def test_rate_limiting():
    """Verify rate limiter middleware triggers HTTP 429 when threshold exceeded."""
    with patch("backend_api.gateway_service.main.redis_client") as mock_redis:
        # Mock pipeline to return a value over threshold
        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [101, True]  # 101 requests is over the 100 limit
        mock_redis.pipeline.return_value = mock_pipe

        response = client.get("/health")
        assert response.status_code == 429
        assert "Too Many Requests" in response.json()["detail"]

def test_route_authentication():
    """Verify auth middleware blocks protected endpoints for unauthenticated requests."""
    response = client.get("/analytics/threat_summary")
    # Gateway routes through security handlers
    assert response.status_code == 401
