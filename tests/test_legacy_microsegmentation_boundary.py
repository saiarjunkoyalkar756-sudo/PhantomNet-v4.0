from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.microsegmentation_service import main as legacy_microsegmentation


ROOT = Path(__file__).resolve().parents[1]
MICROSEGMENTATION_MAIN_PATH = ROOT / "backend_api/microsegmentation_service/main.py"


def test_legacy_microsegmentation_service_has_no_required_upstream_dependencies():
    assert legacy_microsegmentation.app.state.required_dependencies == ()


def test_legacy_microsegmentation_entrypoint_does_not_import_kafka_or_graph_components():
    source = MICROSEGMENTATION_MAIN_PATH.read_text(encoding="utf-8")

    assert "KafkaConsumer" not in source
    assert "network_graph" not in source
    assert "kafka_consumer_thread" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/network/segmentation"),
        ("post", "/api/v1/network/segmentation"),
        ("get", "/api/v1/network/topology"),
        ("get", "/api/v1/network/violations"),
        ("get", "/api/v1/network/threats"),
    ],
)
async def test_legacy_microsegmentation_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_microsegmentation.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-microsegmentation.test") as client:
        response = await client.request(method.upper(), path, json={})

    body = json.loads(response.content)
    assert response.status_code == 410
    assert body["error"]["code"] == "LEGACY_MICROSEGMENTATION_API_RETIRED"
