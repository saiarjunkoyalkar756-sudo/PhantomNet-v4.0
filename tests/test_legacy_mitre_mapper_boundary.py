from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.mitre_attack_mapper import app as legacy_mitre_mapper


ROOT = Path(__file__).resolve().parents[1]
MITRE_MAPPER_APP_PATH = ROOT / "backend_api/mitre_attack_mapper/app.py"


def test_legacy_mitre_mapper_has_no_required_upstream_dependencies():
    assert legacy_mitre_mapper.app.state.required_dependencies == ()


def test_legacy_mitre_mapper_entrypoint_does_not_retain_dataset_or_mapping_components():
    source = MITRE_MAPPER_APP_PATH.read_text(encoding="utf-8")

    assert "load_mitre_data" not in source
    assert "map_event_to_techniques" not in source
    assert "MITRE_DATA_FILE" not in source
    assert "json.load" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/techniques"),
        ("post", "/map_event"),
    ],
)
async def test_legacy_mitre_mapper_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_mitre_mapper.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-mitre-mapper.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_MITRE_MAPPER_API_RETIRED"
