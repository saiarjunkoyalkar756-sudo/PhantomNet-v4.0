from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend_api.security.zero_trust_manager import IntegratedZeroTrustManager


def _request(headers: dict[str, str]) -> SimpleNamespace:
    return SimpleNamespace(
        headers=headers,
        url=SimpleNamespace(path="/api/governed-resource"),
        method="POST",
        client=SimpleNamespace(host="127.0.0.1"),
    )


@pytest.mark.asyncio
async def test_zero_trust_requires_bearer_authentication():
    manager = IntegratedZeroTrustManager()

    with pytest.raises(HTTPException, match="Authentication required") as exc_info:
        await manager.verify_request(_request({"X-Client-Cert-Fingerprint": "test-fingerprint"}))

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_zero_trust_denies_non_allowed_engine_outcome():
    manager = IntegratedZeroTrustManager()
    manager.engine.evaluate_access_request = AsyncMock(
        return_value=SimpleNamespace(
            enforced_action="step_up_authentication",
            details={"trust_score_at_request": 0.3},
        )
    )

    with pytest.raises(HTTPException, match="Zero-Trust Policy Violation") as exc_info:
        await manager.verify_request(_request({"Authorization": "Bearer test-token"}))

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_zero_trust_returns_identity_and_trust_score_after_allowed_evaluation():
    manager = IntegratedZeroTrustManager()
    manager.engine.evaluate_access_request = AsyncMock(
        return_value=SimpleNamespace(
            enforced_action="allowed",
            details={"trust_score_at_request": 0.9},
        )
    )

    result = await manager.verify_request(
        _request(
            {
                "Authorization": "Bearer test-token",
                "X-Client-Cert-Fingerprint": "test-fingerprint",
                "X-Device-Health": "healthy",
            }
        )
    )

    assert result == {"user_id": "user_placeholder", "trust_score": 0.9}
