import pytest

from backend_api.ai_behavioral_engine import main as behavioral_engine


def test_process_event_records_event_for_forecasting_without_emitting_response_actions(monkeypatch):
    monkeypatch.setattr(behavioral_engine, "all_events", [])
    event = {
        "event_id": "behavioral-test-001",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "type": "packet_metadata",
        "data": {"source_ip": "1.2.3.4", "destination_port": 80},
    }

    behavioral_engine.process_event(event)

    assert behavioral_engine.all_events == [event]


@pytest.mark.asyncio
async def test_consumer_is_disabled_in_safe_mode(monkeypatch):
    monkeypatch.setattr(behavioral_engine, "SAFE_MODE", True)
    monkeypatch.setattr(behavioral_engine, "consumer", None, raising=False)

    result = await behavioral_engine.consume_and_process_kafka_messages()

    assert result is None


@pytest.mark.asyncio
async def test_detailed_health_reports_disabled_kafka_when_safe_mode(monkeypatch):
    monkeypatch.setattr(behavioral_engine, "KAFKA_SAFE_MODE", True)
    monkeypatch.setattr(behavioral_engine, "KAFKA_SAFE_MODE_REASON", "Running in SAFE_MODE")
    monkeypatch.setattr(behavioral_engine, "ML_SAFE_MODE", False)

    response = await behavioral_engine.health_detailed()

    assert response["success"] is True
    assert response["data"]["status"] == "degraded"
    assert response["data"]["details"]["kafka"] == "Running in SAFE_MODE"
