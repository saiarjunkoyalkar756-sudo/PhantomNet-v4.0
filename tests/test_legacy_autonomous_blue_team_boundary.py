from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.autonomous_blue_team import main as legacy_autonomous_blue_team


ROOT = Path(__file__).resolve().parents[1]
AUTONOMOUS_BLUE_TEAM_APP_PATH = ROOT / "backend_api/autonomous_blue_team/main.py"
AUTONOMOUS_BLUE_TEAM_CONSUMER_PATH = ROOT / "backend_api/autonomous_blue_team/consumer.py"
AUTONOMOUS_BLUE_TEAM_DEFENSE_MODULES_PATH = ROOT / "backend_api/autonomous_blue_team/defense_modules.py"
AUTONOMOUS_BLUE_TEAM_DOCKERFILE_PATH = ROOT / "backend_api/autonomous_blue_team/Dockerfile"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


def test_legacy_autonomous_blue_team_has_no_required_upstream_dependencies():
    assert legacy_autonomous_blue_team.app.state.required_dependencies == ()


def test_legacy_autonomous_blue_team_entrypoint_does_not_retain_action_or_consumer_components():
    source = AUTONOMOUS_BLUE_TEAM_APP_PATH.read_text(encoding="utf-8")

    assert "start_kafka_consumer" not in source
    assert "ACTION_HISTORY_DIR" not in source
    assert "take_defensive_action" not in source
    assert "open(result_file" not in source
    assert not AUTONOMOUS_BLUE_TEAM_CONSUMER_PATH.exists()
    assert not AUTONOMOUS_BLUE_TEAM_DEFENSE_MODULES_PATH.exists()
    assert not AUTONOMOUS_BLUE_TEAM_DOCKERFILE_PATH.exists()
    assert "autonomous-blue-team:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/take_action"),
        ("get", "/action_history/example"),
        ("get", "/action_list"),
    ],
)
async def test_legacy_autonomous_blue_team_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_autonomous_blue_team.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-autonomous-blue-team.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_AUTONOMOUS_BLUE_TEAM_API_RETIRED"
