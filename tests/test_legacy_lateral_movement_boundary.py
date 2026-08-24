from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.lateral_movement_detector import main as legacy_lateral_movement


ROOT = Path(__file__).resolve().parents[1]
LATERAL_MOVEMENT_APP_PATH = ROOT / "backend_api/lateral_movement_detector/main.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"
LATERAL_MOVEMENT_DOCKERFILE = ROOT / "backend_api/lateral_movement_detector/Dockerfile"


def test_legacy_lateral_movement_has_no_container_or_compose_surface():
    assert not LATERAL_MOVEMENT_DOCKERFILE.exists()
    assert "lateral-movement-detector:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_lateral_movement_has_no_required_upstream_dependencies():
    assert legacy_lateral_movement.app.state.required_dependencies == ()


def test_legacy_lateral_movement_entrypoint_does_not_retain_direct_detector_components():
    source = LATERAL_MOVEMENT_APP_PATH.read_text(encoding="utf-8")

    assert "NormalizedLogEvent" not in source
    assert "is_ip_internal" not in source
    assert "LateralMovementDetectionRequest" not in source
    assert "APIRouter" not in source


@pytest.mark.asyncio
async def test_legacy_lateral_movement_detect_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_lateral_movement.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-lateral-movement.test") as client:
        response = await client.post("/api/v1/lateral-movement/detect/", json={"events": []})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_LATERAL_MOVEMENT_API_RETIRED"
