import pytest
from fastapi.testclient import TestClient

from backend_api.honeypot_service.main import app


@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/honeypots"),
        ("get", "/honeypots"),
        ("post", "/honeypots/legacy/stop"),
        ("get", "/honeypots/legacy/events"),
    ],
)
def test_legacy_honeypot_lifecycle_routes_are_retired(api_client, method: str, path: str):
    response = api_client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "LEGACY_HONEYPOT_API_RETIRED"


def test_standard_health_and_metrics_remain_available(api_client):
    assert api_client.get("/health").status_code == 200
    assert api_client.get("/metrics").status_code == 200
