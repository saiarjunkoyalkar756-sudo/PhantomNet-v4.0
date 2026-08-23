from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.chatbot_service import main as legacy_chatbot


ROOT = Path(__file__).resolve().parents[1]
CHATBOT_APP_PATH = ROOT / "backend_api/chatbot_service/main.py"
CHATBOT_ROUTER_PATH = ROOT / "backend_api/chatbot_service/api.py"


def test_legacy_chatbot_has_no_required_upstream_dependencies():
    assert legacy_chatbot.app.state.required_dependencies == ()


def test_legacy_chatbot_sources_do_not_retain_prompt_or_countermeasure_components():
    source = CHATBOT_APP_PATH.read_text(encoding="utf-8") + CHATBOT_ROUTER_PATH.read_text(encoding="utf-8")

    assert "get_current_user" not in source
    assert "generate_countermeasure" not in source
    assert "generate_signatures" not in source
    assert "compute_score" not in source
    assert "ChatbotQuery" not in source


@pytest.mark.asyncio
async def test_legacy_chatbot_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_chatbot.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-chatbot.test") as client:
        response = await client.post(
            "/chatbot",
            json={"query": "recommend a countermeasure", "attack_event": {}},
        )

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_CHATBOT_API_RETIRED"
