from __future__ import annotations

import json

from fastapi.testclient import TestClient

from backend_api.ai_behavioral_engine import main as behavioral_engine


client = TestClient(behavioral_engine.app)


def test_legacy_behavioral_worker_no_longer_retains_process_local_forecasting_state():
    assert not hasattr(behavioral_engine, "all_events")
    assert not hasattr(behavioral_engine, "process_event")


def test_legacy_behavioral_worker_no_longer_starts_a_kafka_consumer():
    assert not hasattr(behavioral_engine, "consume_and_process_kafka_messages")
    assert behavioral_engine.app.state.required_dependencies == ()


def test_legacy_behavioral_worker_detailed_health_route_is_retired():
    response = client.get("/health_detailed")

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_AI_BEHAVIORAL_API_RETIRED"
