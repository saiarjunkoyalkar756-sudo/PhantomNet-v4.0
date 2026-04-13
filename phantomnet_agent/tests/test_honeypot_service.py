# tests/test_honeypot_service.py
import pytest
import asyncio
import socket
import time
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend_api.honeypot_service.main import app
from backend_api.honeypot_service.manager import honeypot_manager
from backend_api.honeypot_service.models import HoneypotConfig, HoneypotCreate
from backend_api.honeypot_service.metrics import (
    honeypot_sessions_total,
    honeypot_events_total,
    honeypot_errors_total,
    honeypot_active_instances
)
from prometheus_client import generate_latest, REGISTRY

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_prometheus_registry():
    """Fixture to reset Prometheus default registry before each test."""
    # This is a hacky way to clear metrics, but necessary for isolated tests
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    # Re-register default collectors if needed, or re-initialize custom ones
    # For this test, we re-import the metrics which re-registers them.
    from backend_api.honeypot_service import metrics
    yield
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    from backend_api.honeypot_service import metrics

def test_create_honeypot():
    honeypot_create = HoneypotCreate(honeypot_id="test_ssh", type="ssh", port=2222)
    response = client.post("/honeypots", json=honeypot_create.dict())
    assert response.status_code == 200
    honeypot_config = HoneypotConfig(**response.json())
    assert honeypot_config.honeypot_id == "test_ssh"
    assert honeypot_config.status == "running" # Should be running after creation

    # Test creating with existing ID
    response = client.post("/honeypots", json=honeypot_create.dict())
    assert response.status_code == 400

def test_list_honeypots():
    response = client.get("/honeypots")
    assert response.status_code == 200
    honeypots = [HoneypotConfig(**hp) for hp in response.json()]
    assert any(hp.honeypot_id == "test_ssh" for hp in honeypots)

def test_stop_honeypot():
    response = client.post("/honeypots/test_ssh/stop")
    assert response.status_code == 200
    honeypot_config = HoneypotConfig(**response.json())
    assert honeypot_config.honeypot_id == "test_ssh"
    assert honeypot_config.status == "stopped"

    # Test stopping a non-existent honeypot
    response = client.post("/honeypots/non_existent/stop")
    assert response.status_code == 404

def test_get_honeypot_events():
    # Test with a non-existent honeypot first
    response = client.get("/honeypots/non_existent/events")
    assert response.status_code == 404

    # For now, this will return an empty list as there's no event storage yet
    response = client.get("/honeypots/test_ssh/events")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_ssh_honeypot_interaction_and_metrics(reset_prometheus_registry):
    mock_events = []
    
    # Mock the forward_event function
    with patch('backend_api.honeypot_service.forwarder.forward_event', new=lambda event: mock_events.append(event)):
        honeypot_id = "integration_ssh_honeypot"
        honeypot_port = 2223 # Use a different port for integration test
        honeypot_type = "ssh"

        # Assert initial metric state
        metrics_response_before = client.get("/metrics")
        metrics_before_str = metrics_response_before.text
        assert f'honeypot_sessions_total{{honeypot_id="{honeypot_id}",honeypot_type="{honeypot_type}"}} 0.0' in metrics_before_str
        assert f'honeypot_events_total{{honeypot_id="{honeypot_id}",honeypot_type="{honeypot_type}",event_type="auth_attempt"}} 0.0' in metrics_before_str
        assert f'honeypot_active_instances{{honeypot_type="{honeypot_type}"}} 0.0' in metrics_before_str


        # Create honeypot
        honeypot_create = HoneypotCreate(honeypot_id=honeypot_id, type=honeypot_type, port=honeypot_port)
        response = client.post("/honeypots", json=honeypot_create.dict())
        assert response.status_code == 200
        honeypot_config = HoneypotConfig(**response.json())
        assert honeypot_config.honeypot_id == honeypot_id
        assert honeypot_config.status == "running"

        # Give honeypot a moment to start
        await asyncio.sleep(1)

        # Assert metrics after creation
        metrics_response_after_create = client.get("/metrics")
        metrics_after_create_str = metrics_response_after_create.text
        assert f'honeypot_active_instances{{honeypot_type="{honeypot_type}"}} 1.0' in metrics_after_create_str

        # Simulate SSH connection
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", honeypot_port)
            
            # Receive banner
            banner = await asyncio.wait_for(reader.readuntil(b'\r\n'), timeout=5)
            assert b"SSH-2.0" in banner

            # Send a mock username/password
            writer.write(b"username\r\n")
            writer.write(b"password\r\n")
            await writer.drain()
            await asyncio.sleep(0.5) # Give time for honeypot to process

            writer.close()
            await writer.wait_closed()
        except Exception as e:
            pytest.fail(f"SSH client simulation failed: {e}")

        # Give time for event forwarding
        await asyncio.sleep(1)

        # Assert captured events
        assert len(mock_events) >= 1
        auth_event = next((e for e in mock_events if e.get("event_type") == "auth_attempt"), None)
        assert auth_event is not None
        assert auth_event["honeypot_id"] == honeypot_id
        assert auth_event["src_ip"] == "127.0.0.1"
        assert "username=username, password=password" in auth_event["payload"]
        
        # Assert metrics after interaction
        metrics_response_after_interact = client.get("/metrics")
        metrics_after_interact_str = metrics_response_after_interact.text
        assert f'honeypot_sessions_total{{honeypot_id="{honeypot_id}",honeypot_type="{honeypot_type}"}} 1.0' in metrics_after_interact_str
        assert f'honeypot_events_total{{honeypot_id="{honeypot_id}",honeypot_type="{honeypot_type}",event_type="auth_attempt"}} 1.0' in metrics_after_interact_str

        # Stop honeypot
        response = client.post(f"/honeypots/{honeypot_id}/stop")
        assert response.status_code == 200
        stopped_honeypot_config = HoneypotConfig(**response.json())
        assert stopped_honeypot_config.status == "stopped"

        # Assert metrics after stopping
        metrics_response_after_stop = client.get("/metrics")
        metrics_after_stop_str = metrics_response_after_stop.text
        assert f'honeypot_active_instances{{honeypot_type="{honeypot_type}"}} 0.0' in metrics_after_stop_str

