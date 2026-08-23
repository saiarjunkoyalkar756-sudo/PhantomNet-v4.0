from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend_api.gateway_service.main import app


ROOT = Path(__file__).resolve().parents[1]
IAM_API_SOURCE = ROOT / "backend_api/iam_service/api.py"
RETIRED_CODE = "LEGACY_SIMULATED_PASSWORD_RESET_RETIRED"


def _client_with_gateway_middleware_bypassed() -> TestClient:
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value.execute.return_value = [1, True]
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    rate_limit_patch = patch("backend_api.gateway_service.main.redis_client", mock_redis)
    session_patch = patch("backend_api.gateway_service.main.SessionLocal", return_value=mock_session)
    rate_limit_patch.start()
    session_patch.start()
    client = TestClient(app)
    client._phantomnet_rate_limit_patch = rate_limit_patch  # type: ignore[attr-defined]
    client._phantomnet_session_patch = session_patch  # type: ignore[attr-defined]
    return client


def test_iam_source_removes_simulated_password_reset_credential_components():
    source = IAM_API_SOURCE.read_text(encoding="utf-8")

    for unsafe_component in (
        "PasswordResetToken",
        "PasswordResetRequest",
        "PasswordResetConfirm",
        '"type": "password_reset"',
        'data={"token": token}',
        "Password reset email sent (simulated).",
    ):
        assert unsafe_component not in source

    ast.parse(source, filename=str(IAM_API_SOURCE))


def test_simulated_password_reset_routes_fail_closed_at_the_gateway_boundary():
    client = _client_with_gateway_middleware_bypassed()
    try:
        responses = [
            client.post("/api/auth/request-password-reset", json={"username": "user@example.test"}),
            client.post(
                "/api/auth/confirm-password-reset",
                json={"token": "simulated-token", "new_password": "replacement-password"},
            ),
        ]
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert [response.status_code for response in responses] == [410, 410]
    assert all(response.json()["error"]["code"] == RETIRED_CODE for response in responses)
