import pytest
from unittest.mock import MagicMock
import datetime
from .main import get_current_user, get_db
from shared.database import AttackLog


@pytest.fixture
def authenticated_client(client):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.role = "admin"
    client.app.dependency_overrides[get_current_user] = lambda: mock_user
    return client


def test_get_logs_authenticated(authenticated_client, client):
    # Use the client to register a user with known credentials for authentication
    # The authenticated_client fixture handles logging in.
    
    # Directly use the client to post logs, which will use the overridden get_db
    # We need to explicitly get a db session to add logs because authenticated_client's app is what
    # has the dependency overrides, but we need to interact with the database directly in the test to set up data.
    # The get_db fixture in conftest.py returns a session for direct use in tests.
    db = next(authenticated_client.app.dependency_overrides[get_db]())
    log_entry = AttackLog(ip="127.0.0.1", port=80, data="test log entry 1", attack_type="test", confidence_score=0.9, is_anomaly=True, anomaly_score=0.9, is_verified_threat=True, is_blacklisted=False, timestamp=datetime.datetime.now())
    db.add(log_entry)
    db.commit()
    db.close() # Close the session used for setup

    response = authenticated_client.get("/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert len(data["logs"]) == 1
    assert data["logs"][0]["data"] == "test log entry 1"
