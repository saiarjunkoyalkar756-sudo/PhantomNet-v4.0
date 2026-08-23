from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.playbook_flow_builder import main as legacy_playbook_builder


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK_BUILDER_APP_PATH = ROOT / "backend_api/playbook_flow_builder/main.py"


def test_legacy_playbook_builder_has_no_required_upstream_dependencies():
    assert legacy_playbook_builder.app.state.required_dependencies == ()


def test_legacy_playbook_builder_entrypoint_does_not_retain_flow_conversion_components():
    source = PLAYBOOK_BUILDER_APP_PATH.read_text(encoding="utf-8")

    assert "PlaybookFlow" not in source
    assert "convert_flow_to_steps" not in source
    assert "FlowConversionError" not in source
    assert "APIRouter" not in source


@pytest.mark.asyncio
async def test_legacy_playbook_builder_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_playbook_builder.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-playbook-builder.test") as client:
        response = await client.post("/api/v1/playbook-builder/convert", json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_PLAYBOOK_FLOW_BUILDER_API_RETIRED"
