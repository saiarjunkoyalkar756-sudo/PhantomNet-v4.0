from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.ai_agent_orchestrator import main as legacy_ai_agent_orchestrator


ROOT = Path(__file__).resolve().parents[1]
AI_AGENT_ORCHESTRATOR_APP_PATH = ROOT / "backend_api/ai_agent_orchestrator/main.py"


def test_legacy_ai_agent_orchestrator_has_no_required_upstream_dependencies():
    assert legacy_ai_agent_orchestrator.app.state.required_dependencies == ()


def test_legacy_ai_agent_orchestrator_entrypoint_does_not_retain_agent_planning_components():
    source = AI_AGENT_ORCHESTRATOR_APP_PATH.read_text(encoding="utf-8")

    assert "AgentBrain" not in source
    assert "reason_and_plan" not in source
    assert "TaskRequest" not in source
    assert "brain =" not in source


@pytest.mark.asyncio
async def test_legacy_ai_agent_orchestrator_task_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_ai_agent_orchestrator.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-ai-agent-orchestrator.test") as client:
        response = await client.post(
            "/agents/task",
            json={"task_description": "isolate a host", "agent_persona": "sentinel"},
        )

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_AI_AGENT_ORCHESTRATOR_API_RETIRED"
