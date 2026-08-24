from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.soar_engine import app as soar_engine


ROOT = Path(__file__).resolve().parents[1]
SOAR_ENGINE_PATH = ROOT / "backend_api/soar_engine/app.py"
RAW_SOAR_WORKER_PATHS = (
    ROOT / "backend_api/soar_engine/main.py",
    ROOT / "backend_api/soar_engine/playbooks.py",
    ROOT / "backend_api/soar_engine/countermeasures.py",
    ROOT / "backend_api/soar_engine/Dockerfile",
    ROOT / "backend_api/soar_engine/consumer.py",
)


def test_soar_engine_has_no_raw_kafka_direct_action_worker_or_container():
    assert all(not path.exists() for path in RAW_SOAR_WORKER_PATHS)


def test_soar_engine_declares_database_only_readiness_for_retained_governed_containment():
    assert soar_engine.app.state.required_dependencies == ("database",)


def test_soar_engine_source_does_not_retain_legacy_executor_or_approval_components():
    source = SOAR_ENGINE_PATH.read_text(encoding="utf-8")

    assert "SOARPlaybookEngine" not in source
    assert "AIPlaybookGenerator" not in source
    assert "AutoResponseEngine" not in source
    assert "HumanInTheLoop" not in source
    assert "consume_kafka_messages" not in source
    assert "execute_playbook" not in source


def test_soar_engine_retains_governed_containment_router_before_legacy_catch_all():
    route_paths = [getattr(route, "path", "") for route in soar_engine.app.routes]

    assert "/api/soar/governed-containment/requests" in route_paths
    assert "/api/{legacy_path:path}" in route_paths


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/soar/playbooks"),
        ("post", "/api/soar/playbooks/example/execute"),
        ("post", "/api/soar/playbooks/generate"),
        ("post", "/api/soar/approvals/example/approve"),
    ],
)
async def test_legacy_soar_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=soar_engine.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-soar.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_SOAR_API_RETIRED"
