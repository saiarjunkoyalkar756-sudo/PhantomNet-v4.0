# tests/test_lateral_movement.py
import pytest
from fastapi.testclient import TestClient
from backend_api.lateral_movement_detector.main import app, is_ip_internal

client = TestClient(app)

def test_is_ip_internal():
    """Verify IP subnet classification logic."""
    assert is_ip_internal("127.0.0.1") is True
    assert is_ip_internal("10.0.0.5") is True
    assert is_ip_internal("192.168.1.100") is True
    assert is_ip_internal("8.8.8.8") is False
    assert is_ip_internal("203.0.113.50") is False

def test_external_ssh_to_critical_host_detected():
    """Verify that external SSH connection to critical servers raises a critical alert."""
    payload = {
        "events": [
            {
                "event_id": "evt-1234",
                "timestamp": "2026-05-28T07:00:00Z",
                "event_type": "auth",
                "action": "login_success",
                "protocol": "ssh",
                "source_ip": "203.0.113.15",  # External IP
                "source_host": "external-machine",
                "destination_host": "database-prod",  # Critical host (prod keyword)
                "destination_port": 22,
                "user": "root",
                "severity": "Informational",
                "message": "SSH login success",
                "source_type": "system_logs",
                "original_raw_log": "raw log here"
            }
        ]
    }
    response = client.post("/api/v1/lateral-movement/detect/", json=payload)
    assert response.status_code == 200
    detections = response.json()["data"]["detections"]
    assert len(detections) == 1
    assert detections[0]["severity"].lower() == "critical"
    assert "ssh" in detections[0]["description"].lower()

def test_psexec_to_domain_controller_detected():
    """Verify that remote PSExec service execution triggers a high severity alert."""
    payload = {
        "events": [
            {
                "event_id": "evt-5678",
                "timestamp": "2026-05-28T07:05:00Z",
                "event_type": "process",
                "action": "start",
                "process_name": "psexec.exe",
                "source_host": "workstation-5",
                "metadata": {"remote_target": "domain-controller"},
                "message": "psexec.exe -i -d cmd.exe",
                "severity": "Informational",
                "source_type": "system_logs",
                "original_raw_log": "raw log here"
            }
        ]
    }
    response = client.post("/api/v1/lateral-movement/detect/", json=payload)
    assert response.status_code == 200
    detections = response.json()["data"]["detections"]
    assert len(detections) == 1
    assert detections[0]["severity"].lower() == "high"
    assert "psexec" in detections[0]["description"].lower()
