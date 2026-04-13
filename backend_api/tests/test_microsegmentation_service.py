import pytest
from fastapi.testclient import TestClient
from backend_api.microsegmentation_service.service import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_network_segments(client):
    response = client.get("/api/v1/network/segmentation")
    assert response.status_code == 200
    assert response.json() == [
        {"id": "1", "name": "HR", "subnets": ["10.0.1.0/24"]},
        {"id": "2", "name": "Finance", "subnets": ["10.0.2.0/24"]},
        {"id": "3", "name": "Engineering", "subnets": ["10.0.3.0/24"]},
    ]

def test_create_network_segment(client):
    segment_data = {"id": "4", "name": "Marketing", "subnets": ["10.0.4.0/24"]}
    response = client.post("/api/v1/network/segmentation", json=segment_data)
    assert response.status_code == 200
    assert response.json() == segment_data

def test_get_segmentation_violations(client):
    response = client.get("/api/v1/network/violations")
    assert response.status_code == 200
    assert response.json() == [
        {"id": "1", "timestamp": "2025-12-10T10:00:00Z", "source_ip": "10.0.1.10", "destination_ip": "10.0.2.15", "description": "Unauthorized communication from HR to Finance"},
    ]

def test_get_network_topology(client):
    # This is a bit tricky to test without a running Kafka consumer.
    # For now, we'll just check that the endpoint returns an empty graph.
    response = client.get("/api/v1/network/topology")
    assert response.status_code == 200
    assert response.json() == {"nodes": [], "links": []}

def test_get_network_threats(client):
    response = client.get("/api/v1/network/threats")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "type": "Port Scan", "source": "1.2.3.4", "timestamp": "2025-12-10 10:30 AM"},
        {"id": 2, "type": "DDoS Attempt", "source": "5.6.7.8", "timestamp": "2025-12-10 09:15 AM"},
        {"id": 3, "type": "C2 Beaconing", "source": "9.10.11.12", "timestamp": "2025-12-10 08:45 AM"},
    ]