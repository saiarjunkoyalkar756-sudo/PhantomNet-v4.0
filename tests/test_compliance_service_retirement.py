"""Source-contract regressions for the retired standalone compliance API."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.compliance_service import main as legacy_compliance


ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE_MAIN = ROOT / "backend_api/compliance_service/main.py"
SHARED_COMPLIANCE_ENGINE = ROOT / "backend_api/shared/compliance_engine.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"
COMPLIANCE_RETIRED_PATHS = (
    ROOT / "backend_api/compliance_service/crud.py",
    ROOT / "backend_api/compliance_service/database.py",
    ROOT / "backend_api/compliance_service/models.py",
    ROOT / "backend_api/compliance_service/Dockerfile",
)


def test_legacy_compliance_has_no_persistence_or_deployment_surface():
    assert all(not path.exists() for path in COMPLIANCE_RETIRED_PATHS)
    assert "compliance-service:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_compliance_service_has_no_database_cache_or_crud_dependencies():
    source = COMPLIANCE_MAIN.read_text(encoding="utf-8")

    assert legacy_compliance.app.state.required_dependencies == ()
    assert "get_db" not in source
    assert "from . import crud" not in source
    assert "redis_client" not in source
    assert "ComplianceStandard" not in source
    assert "ComplianceAssessment" not in source


def test_legacy_compliance_status_and_shared_utility_boundary_are_explicit():
    legacy_source = COMPLIANCE_MAIN.read_text(encoding="utf-8")
    shared_engine_source = SHARED_COMPLIANCE_ENGINE.read_text(encoding="utf-8")

    assert 'code=RETIREMENT_CODE' in legacy_source
    assert 'status_code=status.HTTP_410_GONE' in legacy_source
    assert '"status": "legacy-compliance-api-retired"' in legacy_source
    assert "tenant scope, authorization, evidence provenance, or governed" in legacy_source
    assert "class ComplianceEngine" in shared_engine_source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/standards/", {"name": "ISO 27001"}),
        ("get", "/standards/", None),
        ("get", "/standards/ISO%2027001", None),
        ("post", "/assessments/", {"standard_name": "ISO 27001"}),
        ("get", "/assessments/", None),
        ("get", "/assessments/assessment-001", None),
        ("put", "/assessments/assessment-001", {"status": "completed"}),
    ],
)
async def test_legacy_compliance_routes_fail_closed_at_the_asgi_boundary(
    method: str, path: str, payload: object | None
):
    transport = httpx.ASGITransport(app=legacy_compliance.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-compliance.test") as client:
        response = await client.request(method.upper(), path, json=payload)

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == legacy_compliance.RETIREMENT_CODE
