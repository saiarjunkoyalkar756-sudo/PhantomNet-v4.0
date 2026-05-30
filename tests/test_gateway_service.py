# tests/test_gateway_service.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from backend_api.gateway_service.main import app

from backend_api.shared.database import get_db

client = TestClient(app)

async def mock_get_db_dependency():
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()
    yield mock_session

app.dependency_overrides[get_db] = mock_get_db_dependency

@pytest.fixture(autouse=True)
def mock_db_session():
    with patch("backend_api.gateway_service.main.SessionLocal") as mock_session_cls, \
         patch("backend_api.shared.database.AsyncSessionLocal") as mock_async_session_cls:
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session_cls.return_value = mock_session
        
        mock_async_session = MagicMock()
        mock_async_session.execute = AsyncMock()
        mock_async_session.commit = AsyncMock()
        mock_async_session.rollback = AsyncMock()
        mock_async_session.close = AsyncMock()
        mock_async_session.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_async_session.__aexit__ = AsyncMock()
        mock_async_session_cls.return_value = mock_async_session
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
