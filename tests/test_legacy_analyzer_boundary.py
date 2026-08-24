from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.analyzer import app as legacy_analyzer


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_DIR = ROOT / "backend_api/analyzer"
ANALYZER_APP_PATH = ANALYZER_DIR / "app.py"


def test_legacy_analyzer_has_no_required_upstream_dependencies():
    assert legacy_analyzer.app.state.required_dependencies == ()


def test_legacy_analyzer_entrypoint_does_not_retain_chat_or_consumer_components():
    source = ANALYZER_APP_PATH.read_text(encoding="utf-8")

    assert "neural_threat_brain" not in source
    assert "brain.chat" not in source
    assert "threading.Thread" not in source
    assert "consumer.main" not in source
    assert not (ANALYZER_DIR / "consumer.py").exists()
    assert not (ANALYZER_DIR / "model.py").exists()
    assert not (ANALYZER_DIR / "neural_threat_brain.py").exists()
    assert not (ANALYZER_DIR / "Dockerfile").exists()
    assert not (ANALYZER_DIR / "requirements.txt").exists()


@pytest.mark.asyncio
async def test_legacy_analyzer_chat_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_analyzer.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-analyzer.test") as client:
        response = await client.post("/chat", json={"message": "analyze this"})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_ANALYZER_API_RETIRED"
