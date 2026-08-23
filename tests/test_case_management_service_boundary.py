from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import yaml

from backend_api.case_management_service import app as case_app


ROOT = Path(__file__).resolve().parents[1]
CASE_APP_PATH = ROOT / "backend_api/case_management_service/app.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


def test_case_management_declares_database_only_readiness_and_exposes_governed_routes():
    assert case_app.app.state.required_dependencies == ("database",)

    routes = {
        route.path: route.methods
        for route in case_app.app.routes
        if getattr(route, "methods", None)
    }
    assert "/governed-cases/from-alert/{alert_id}" in routes
    assert "/governed-cases/playbook-runs/{run_id}/approve" in routes
    assert "POST" in routes["/governed-cases/playbook-runs/{run_id}/approve"]


def test_case_management_compose_healthcheck_uses_dependency_aware_ready_route():
    compose = yaml.safe_load(ROOT_COMPOSE_PATH.read_text(encoding="utf-8"))
    healthcheck = compose["services"]["case-management-service"]["healthcheck"]

    assert healthcheck["test"][0] == "CMD-SHELL"
    assert "/ready" in healthcheck["test"][1]
    assert healthcheck["timeout"] == "5s"
    assert healthcheck["retries"] == 3


def test_case_management_app_does_not_import_or_start_the_untenant_scoped_legacy_store():
    source = CASE_APP_PATH.read_text(encoding="utf-8")

    assert "from .database import" not in source
    assert "create_cases_table" not in source
    assert "get_all_cases" not in source


@pytest.mark.asyncio
async def test_case_management_startup_initializes_only_governed_workflow_store(monkeypatch):
    initialized: list[bool] = []

    async def fake_initialize() -> None:
        initialized.append(True)

    monkeypatch.setattr(case_app, "init_case_workflow_store", fake_initialize)
    await case_app.case_startup(case_app.app)

    assert initialized == [True]


@pytest.mark.asyncio
async def test_legacy_case_routes_fail_closed_with_a_migration_signal():
    transport = httpx.ASGITransport(app=case_app.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://case-management.test") as client:
        response = await client.post("/cases", json={"title": "legacy bypass", "severity": "critical"})

    payload = json.loads(response.content)
    assert response.status_code == 410
    assert payload["error"]["code"] == "LEGACY_CASE_API_RETIRED"
    assert "/governed-cases" in payload["error"]["message"]


def test_governed_case_playbook_transitions_remain_approval_bound_in_source():
    source = CASE_APP_PATH.read_text(encoding="utf-8")

    assert 'requires_approval=True' in source
    assert 'require_capability("response:approve")' in source
    assert 'transition_playbook(\n            str(current_user.tenant_id), run_id, "approved"' in source
