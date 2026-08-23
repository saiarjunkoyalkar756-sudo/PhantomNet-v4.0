from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.cloud_security_service import app as legacy_cloud_security


ROOT = Path(__file__).resolve().parents[1]
CLOUD_SECURITY_APP_PATH = ROOT / "backend_api/cloud_security_service/app.py"


def test_legacy_cloud_security_has_no_required_upstream_dependencies():
    assert legacy_cloud_security.app.state.required_dependencies == ()


def test_legacy_cloud_security_entrypoint_does_not_accept_cloud_credentials_or_create_clients():
    source = CLOUD_SECURITY_APP_PATH.read_text(encoding="utf-8")

    assert "aws_secret_access_key" not in source
    assert "aws_access_key_id" not in source
    assert "boto3" not in source
    assert "list_buckets" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/aws/misconfiguration",
        "/aws/iam_abuse",
        "/aws/s3_exposure",
    ],
)
async def test_legacy_cloud_security_routes_fail_closed_at_the_asgi_boundary(path: str):
    transport = httpx.ASGITransport(app=legacy_cloud_security.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-cloud-security.test") as client:
        response = await client.post(path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_CLOUD_SECURITY_API_RETIRED"
