from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.ai_behavioral_engine import app as legacy_ai_behavioral_api
from backend_api.ai_behavioral_engine import main as legacy_ai_behavioral_worker


ROOT = Path(__file__).resolve().parents[1]
AI_BEHAVIORAL_API_PATH = ROOT / "backend_api/ai_behavioral_engine/app.py"
AI_BEHAVIORAL_WORKER_PATH = ROOT / "backend_api/ai_behavioral_engine/main.py"


@pytest.mark.parametrize(
    "application",
    [legacy_ai_behavioral_api.app, legacy_ai_behavioral_worker.app],
)
def test_legacy_ai_behavioral_apps_have_no_required_upstream_dependencies(application):
    assert application.state.required_dependencies == ()


def test_legacy_ai_behavioral_sources_do_not_retain_direct_analysis_or_worker_components():
    source = AI_BEHAVIORAL_API_PATH.read_text(encoding="utf-8") + AI_BEHAVIORAL_WORKER_PATH.read_text(encoding="utf-8")

    assert "start_kafka_consumer" not in source
    assert "ResilientKafkaConsumer" not in source
    assert "ThreatForecastingAI" not in source
    assert "RuleBasedIDS" not in source
    assert "UEBAEngine" not in source
    assert "create_task" not in source
    assert "BehavioralEvent" not in source
    assert "health_detailed" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("application", "method", "path"),
    [
        (legacy_ai_behavioral_api.app, "post", "/analyze"),
        (legacy_ai_behavioral_api.app, "get", "/profiles/user/example"),
        (legacy_ai_behavioral_worker.app, "get", "/health_detailed"),
    ],
)
async def test_legacy_ai_behavioral_routes_fail_closed_at_the_asgi_boundary(application, method: str, path: str):
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-ai-behavioral.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_AI_BEHAVIORAL_API_RETIRED"
