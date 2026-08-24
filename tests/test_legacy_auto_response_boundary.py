from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.auto_response_engine import main as legacy_auto_response


ROOT = Path(__file__).resolve().parents[1]
AUTO_RESPONSE_APP_PATH = ROOT / "backend_api/auto_response_engine/main.py"
AUTO_RESPONSE_DOCKERFILE_PATH = ROOT / "backend_api/auto_response_engine/Dockerfile"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


def test_legacy_auto_response_has_no_deployable_container_or_compose_service():
    assert not AUTO_RESPONSE_DOCKERFILE_PATH.exists()
    assert "auto-response-engine:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_auto_response_has_no_required_upstream_dependencies():
    assert legacy_auto_response.app.state.required_dependencies == ()


def test_legacy_auto_response_entrypoint_does_not_retain_simulated_executor():
    source = AUTO_RESPONSE_APP_PATH.read_text(encoding="utf-8")

    assert "execute_playbook_step" not in source
    assert "execute_playbook_run_in_background" not in source
    assert "background_tasks.add_task" not in source
    assert "playbook_crud" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/execute/17",
        "/resume/42/approve",
    ],
)
async def test_legacy_auto_response_routes_fail_closed_at_the_asgi_boundary(path: str):
    transport = httpx.ASGITransport(app=legacy_auto_response.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-auto-response.test") as client:
        response = await client.post(path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_AUTO_RESPONSE_API_RETIRED"
