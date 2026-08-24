from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.bas_engine import main as legacy_bas


ROOT = Path(__file__).resolve().parents[1]
BAS_APP_PATH = ROOT / "backend_api/bas_engine/main.py"
BAS_DOCKERFILE_PATH = ROOT / "backend_api/bas_engine/Dockerfile"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


def test_legacy_bas_has_no_required_upstream_dependencies():
    assert legacy_bas.app.state.required_dependencies == ()


def test_legacy_bas_has_no_container_or_root_compose_surface():
    assert not BAS_DOCKERFILE_PATH.exists()
    assert "bas-engine:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_bas_entrypoint_does_not_retain_simulation_or_local_result_components():
    source = BAS_APP_PATH.read_text(encoding="utf-8")

    assert "run_xss_simulation" not in source
    assert "run_sqli_simulation" not in source
    assert "run_rce_simulation" not in source
    assert "SIMULATION_RESULTS_DIR" not in source
    assert "start_simulation" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/start_simulation"),
        ("get", "/simulation_results/example"),
        ("get", "/simulation_list"),
    ],
)
async def test_legacy_bas_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_bas.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-bas.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_BAS_API_RETIRED"
