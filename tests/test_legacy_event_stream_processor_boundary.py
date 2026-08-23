from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.event_stream_processor import app as legacy_event_stream_processor


ROOT = Path(__file__).resolve().parents[1]
EVENT_STREAM_PROCESSOR_APP_PATH = ROOT / "backend_api/event_stream_processor/app.py"


def test_legacy_event_stream_processor_has_no_required_upstream_dependencies():
    assert legacy_event_stream_processor.app.state.required_dependencies == ()


def test_legacy_event_stream_processor_entrypoint_does_not_retain_query_or_consumer_components():
    source = EVENT_STREAM_PROCESSOR_APP_PATH.read_text(encoding="utf-8")

    assert "start_kafka_consumer" not in source
    assert "get_db_connection" not in source
    assert "psycopg2" not in source
    assert "SELECT * FROM events" not in source


@pytest.mark.asyncio
async def test_legacy_event_stream_processor_logs_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_event_stream_processor.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-event-stream.test") as client:
        response = await client.get("/logs?source_ip__contains=10.0.0")

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_EVENT_STREAM_PROCESSOR_API_RETIRED"
