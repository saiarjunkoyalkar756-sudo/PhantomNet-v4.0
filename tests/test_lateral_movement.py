from __future__ import annotations

import json

from fastapi.testclient import TestClient

from backend_api.lateral_movement_detector.main import app


client = TestClient(app)


def test_legacy_lateral_movement_detector_route_is_retired_for_external_ssh_payloads():
    payload = {
        "events": [
            {
                "event_id": "evt-1234",
                "event_type": "auth",
                "action": "login_success",
                "source_ip": "203.0.113.15",
                "destination_host": "database-prod",
                "destination_port": 22,
            }
        ]
    }

    response = client.post("/api/v1/lateral-movement/detect/", json=payload)

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_LATERAL_MOVEMENT_API_RETIRED"


def test_legacy_lateral_movement_detector_route_is_retired_for_psexec_payloads():
    payload = {
        "events": [
            {
                "event_id": "evt-5678",
                "event_type": "process",
                "process_name": "psexec.exe",
                "metadata": {"remote_target": "domain-controller"},
            }
        ]
    }

    response = client.post("/api/v1/lateral-movement/detect/", json=payload)

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_LATERAL_MOVEMENT_API_RETIRED"
