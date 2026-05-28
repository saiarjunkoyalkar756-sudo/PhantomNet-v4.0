# tests/test_forensics_engine.py
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend_api.forensics_engine.main import app

client = TestClient(app)

def test_build_forensic_timeline_sources_filter():
    """Verify that only requested data sources populate in the timeline."""
    payload = {
        "asset_id": "test-asset",
        "data_sources": ["logs"]
    }
    response = client.post("/timeline/build/", json=payload)
    assert response.status_code == 200
    events = response.json()["data"]["timeline_events"]
    
    # Logs source has 2 events simulated: process_creation and network_connection
    assert len(events) == 2
    for event in events:
        assert event["source"] in ["system_logs", "network_logs"]

def test_build_forensic_timeline_chronological_order():
    """Verify that timeline events are sorted chronologically."""
    payload = {
        "asset_id": "test-asset",
        "data_sources": ["logs", "disk_image"]
    }
    response = client.post("/timeline/build/", json=payload)
    assert response.status_code == 200
    events = response.json()["data"]["timeline_events"]
    assert len(events) == 3
    
    # Check timestamps are ascending
    timestamps = [datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) for e in events]
    assert timestamps == sorted(timestamps)

def test_build_forensic_timeline_time_range_filter():
    """Verify that time-range filters selectively prune timeline events."""
    now = datetime.now(timezone.utc)
    
    # Set start_time to 1 hour and 45 minutes ago.
    # The 3 simulated events are:
    # - disk_image: 3 hours ago (should be excluded)
    # - logs (process_creation): 2 hours ago (should be excluded)
    # - logs (network_connection): 1 hour and 30 minutes ago (should be included)
    start_time = now - timedelta(hours=1, minutes=45)
    
    payload = {
        "asset_id": "test-asset",
        "start_time": start_time.isoformat(),
        "data_sources": ["logs", "disk_image"]
    }
    response = client.post("/timeline/build/", json=payload)
    assert response.status_code == 200
    events = response.json()["data"]["timeline_events"]
    
    assert len(events) == 1
    assert events[0]["event_type"] == "network_connection"
