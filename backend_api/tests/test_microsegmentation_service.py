import json

import httpx
import pytest

from backend_api.microsegmentation_service import main as microsegmentation


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
async def test_legacy_microsegmentation_routes_are_explicitly_retired(method: str, path: str):
    transport = httpx.ASGITransport(app=microsegmentation.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-microsegmentation.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_MICROSEGMENTATION_API_RETIRED"


def test_legacy_microsegmentation_has_no_live_graph_or_broker_state():
    assert microsegmentation.app.state.required_dependencies == ()
    assert not hasattr(microsegmentation, "network_graph")
    assert not hasattr(microsegmentation, "kafka_consumer_thread")
