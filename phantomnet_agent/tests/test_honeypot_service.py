from typing import Dict, List, Optional

import pytest
from fastapi.testclient import TestClient

from backend_api.honeypot_service.main import app
from backend_api.honeypot_service.models import HoneypotConfig, HoneypotCreate
from backend_api.honeypot_service.metrics import honeypot_active_instances


class InMemoryHoneypotManager:
    """Deterministic manager substitute for API-route tests; it never spawns a process."""

    def __init__(self):
        self.honeypots: Dict[str, HoneypotConfig] = {}

    async def start_honeypot(self, config: HoneypotConfig) -> None:
        config.status = "running"
        config.pid = 4242
        self.honeypots[config.honeypot_id] = config

    async def stop_honeypot(self, honeypot_id: str) -> None:
        config = self.honeypots.get(honeypot_id)
        if config is not None:
            config.status = "stopped"
            config.pid = None

    async def get_honeypot_status(self, honeypot_id: str) -> Optional[HoneypotConfig]:
        return self.honeypots.get(honeypot_id)

    async def list_honeypots(self) -> List[HoneypotConfig]:
        return list(self.honeypots.values())


@pytest.fixture
def api_client(monkeypatch):
    manager = InMemoryHoneypotManager()
    honeypot_active_instances.clear()
    monkeypatch.setattr("backend_api.honeypot_service.main.honeypot_manager", manager)
    with TestClient(app) as client:
        yield client
    honeypot_active_instances.clear()


def _honeypot_payload(honeypot_id: str, port: int = 2222) -> dict:
    return HoneypotCreate(honeypot_id=honeypot_id, type="ssh", port=port).model_dump()


def test_create_honeypot(api_client):
    response = api_client.post("/honeypots", json=_honeypot_payload("test_ssh"))
    assert response.status_code == 200
    honeypot_config = HoneypotConfig(**response.json())
    assert honeypot_config.honeypot_id == "test_ssh"
    assert honeypot_config.status == "running"

    assert api_client.post("/honeypots", json=_honeypot_payload("test_ssh")).status_code == 400


def test_list_honeypots(api_client):
    assert api_client.post("/honeypots", json=_honeypot_payload("list_ssh")).status_code == 200
    response = api_client.get("/honeypots")
    assert response.status_code == 200
    assert [HoneypotConfig(**hp).honeypot_id for hp in response.json()] == ["list_ssh"]


def test_stop_honeypot(api_client):
    assert api_client.post("/honeypots", json=_honeypot_payload("stop_ssh")).status_code == 200
    response = api_client.post("/honeypots/stop_ssh/stop")
    assert response.status_code == 200
    assert HoneypotConfig(**response.json()).status == "stopped"
    assert api_client.post("/honeypots/non_existent/stop").status_code == 404


def test_get_honeypot_events(api_client):
    assert api_client.get("/honeypots/non_existent/events").status_code == 404
    assert api_client.post("/honeypots", json=_honeypot_payload("events_ssh")).status_code == 200
    response = api_client.get("/honeypots/events_ssh/events")
    assert response.status_code == 200
    assert response.json() == []


def test_ssh_honeypot_interaction_and_metrics(api_client):
    """Validate the observable service lifecycle metric without cross-process event assumptions.

    TODO: Add a true process-level SSH interaction test only after honeypot child events
    are forwarded to a shared parent-visible store or metrics endpoint. Prometheus metrics
    in the child process cannot be asserted from the parent service registry.
    """
    honeypot_id = "metrics_ssh"
    honeypot_type = "ssh"
    response = api_client.post("/honeypots", json=_honeypot_payload(honeypot_id, port=2223))
    assert response.status_code == 200
    assert f'honeypot_active_instances{{honeypot_type="{honeypot_type}"}} 1.0' in api_client.get("/metrics").text

    response = api_client.post(f"/honeypots/{honeypot_id}/stop")
    assert response.status_code == 200
    assert HoneypotConfig(**response.json()).status == "stopped"
    assert f'honeypot_active_instances{{honeypot_type="{honeypot_type}"}} 0.0' in api_client.get("/metrics").text
