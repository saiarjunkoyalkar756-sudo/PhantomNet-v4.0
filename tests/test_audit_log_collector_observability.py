"""Regression tests for the retired standalone audit-log collector HTTP boundary."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.audit_log_collector import main as audit_main


ROOT = Path(__file__).resolve().parents[1]
AUDIT_COLLECTOR_PATH = ROOT / "backend_api/audit_log_collector/main.py"
GOVERNED_CONTAINMENT_PATH = ROOT / "backend_api/soar_engine/governed_containment.py"
GOVERNED_API_PATH = ROOT / "backend_api/soar_engine/governed_api.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"
AUDIT_COLLECTOR_DOCKERFILE = ROOT / "backend_api/audit_log_collector/Dockerfile"


def test_retired_audit_log_collector_has_no_container_or_compose_surface():
    assert not AUDIT_COLLECTOR_DOCKERFILE.exists()
    assert "audit-log-collector:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_retired_audit_log_collector_has_no_required_upstream_dependencies_or_mutation_dependencies():
    source = AUDIT_COLLECTOR_PATH.read_text(encoding="utf-8")

    assert audit_main.app.state.required_dependencies == ()
    assert "get_db" not in source
    assert "create_audit_log" not in source
    assert "from . import crud" not in source
    assert "submit_alert_to_ledger" not in source


def test_retired_audit_log_collector_status_and_governed_integrity_imports_are_explicit():
    collector_source = AUDIT_COLLECTOR_PATH.read_text(encoding="utf-8")
    governed_containment_source = GOVERNED_CONTAINMENT_PATH.read_text(encoding="utf-8")
    governed_api_source = GOVERNED_API_PATH.read_text(encoding="utf-8")

    assert "code=RETIREMENT_CODE" in collector_source
    assert "status_code=status.HTTP_410_GONE" in collector_source
    assert '"status": "legacy-audit-log-collector-retired"' in collector_source
    assert "tenant scope, authorization, source provenance, or immutable" in collector_source
    assert "from backend_api.audit_log_collector.integrity import GENESIS_HASH, append_record" in governed_containment_source
    assert "from backend_api.audit_log_collector.verification import ContainmentAuditVerifier" in governed_api_source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/ingest/", {"raw_log_data": "untrusted", "action": "alert_created"}),
        ("post", "/ingest/batch", [{"raw_log_data": "untrusted", "action": "alert_created"}]),
        ("get", "/logs/", None),
    ],
)
async def test_legacy_audit_log_collector_routes_fail_closed_at_the_asgi_boundary(
    method: str, path: str, payload: object | None
):
    transport = httpx.ASGITransport(app=audit_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-audit-collector.test") as client:
        response = await client.request(method.upper(), path, json=payload)

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == audit_main.RETIREMENT_CODE
