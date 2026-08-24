from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.soar_playbook_engine import main as legacy_soar


ROOT = Path(__file__).resolve().parents[1]
LEGACY_SOAR_MAIN_PATH = ROOT / "backend_api/soar_playbook_engine/main.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"
LEGACY_SOAR_RETIRED_PATHS = (
    ROOT / "backend_api/soar_playbook_engine/crud.py",
    ROOT / "backend_api/soar_playbook_engine/database.py",
    ROOT / "backend_api/soar_playbook_engine/playbook_model.py",
    ROOT / "backend_api/soar_playbook_engine/Dockerfile",
)


def test_legacy_soar_playbook_service_has_no_required_upstream_dependency():
    assert legacy_soar.app.state.required_dependencies == ()


def test_legacy_soar_has_no_crud_database_model_or_deployment_surface():
    assert all(not path.exists() for path in LEGACY_SOAR_RETIRED_PATHS)
    assert "soar-playbook-engine:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_soar_source_does_not_import_legacy_crud_or_database_sessions():
    source = LEGACY_SOAR_MAIN_PATH.read_text(encoding="utf-8")

    assert "from .database import" not in source
    assert "from . import crud" not in source
    assert "approved_by_human" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/playbooks/", {"name": "legacy-bypass", "steps": []}),
        ("post", "/playbooks/7/run", {}),
        ("post", "/playbook_runs/7", {"status": "completed"}),
        ("post", "/playbook_approvals/", {"playbook_run_id": 7, "approved": True}),
    ],
)
async def test_legacy_soar_playbook_paths_fail_closed(method: str, path: str, payload: dict[str, object]):
    transport = httpx.ASGITransport(app=legacy_soar.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-soar.test") as client:
        response = await getattr(client, method)(path, json=payload)

    body = json.loads(response.content)
    assert response.status_code == 410
    assert body["error"]["code"] == "LEGACY_SOAR_PLAYBOOK_API_RETIRED"
    assert "governed containment" in body["error"]["message"]
