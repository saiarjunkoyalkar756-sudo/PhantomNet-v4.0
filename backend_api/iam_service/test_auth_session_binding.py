"""Regression tests for JWT-to-session and tenant identity binding."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from backend_api.iam_service import auth_methods


TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = UUID("00000000-0000-0000-0000-000000000002")


class _SessionResult:
    def __init__(self, session_record: object) -> None:
        self._session_record = session_record

    def scalar_one_or_none(self) -> object:
        return self._session_record


class _SessionDatabase:
    def __init__(self, session_record: object) -> None:
        self._session_record = session_record

    async def execute(self, _statement: object) -> _SessionResult:
        return _SessionResult(self._session_record)


def _request() -> object:
    return SimpleNamespace(cookies={}, headers={"Authorization": "Bearer controlled-test-token"})


def _claims(tenant_id: UUID = TENANT_ID) -> dict[str, str]:
    return {
        "sub": "security-analyst",
        "role": "analyst",
        "jti": "controlled-session-jti",
        "tenant_id": str(tenant_id),
    }


def _session(user_id: int = 42) -> object:
    return SimpleNamespace(
        user_id=user_id,
        is_valid=True,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )


def _user(user_id: int = 42, tenant_id: UUID = TENANT_ID) -> object:
    return SimpleNamespace(id=user_id, tenant_id=tenant_id, username="security-analyst", role="analyst")


@pytest.mark.asyncio
async def test_current_user_accepts_only_a_session_bound_to_the_authenticated_user_and_tenant(monkeypatch):
    monkeypatch.setattr(auth_methods.jwt, "decode", lambda *_args, **_kwargs: _claims())

    async def get_bound_user(_db: object, username: str) -> object:
        assert username == "security-analyst"
        return _user()

    monkeypatch.setattr(auth_methods, "get_user", get_bound_user)

    authenticated = await auth_methods.get_current_user(_request(), _SessionDatabase(_session()))

    assert authenticated.id == 42
    assert authenticated.tenant_id == TENANT_ID


@pytest.mark.asyncio
async def test_current_user_rejects_a_valid_claim_set_when_the_session_belongs_to_another_user(monkeypatch):
    monkeypatch.setattr(auth_methods.jwt, "decode", lambda *_args, **_kwargs: _claims())

    async def get_bound_user(_db: object, username: str) -> object:
        assert username == "security-analyst"
        return _user()

    monkeypatch.setattr(auth_methods, "get_user", get_bound_user)

    with pytest.raises(HTTPException) as exc_info:
        await auth_methods.get_current_user(_request(), _SessionDatabase(_session(user_id=99)))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_current_user_rejects_a_valid_claim_set_when_the_user_tenant_differs_from_the_token(monkeypatch):
    monkeypatch.setattr(auth_methods.jwt, "decode", lambda *_args, **_kwargs: _claims(TENANT_ID))

    async def get_wrong_tenant_user(_db: object, username: str) -> object:
        assert username == "security-analyst"
        return _user(tenant_id=OTHER_TENANT_ID)

    monkeypatch.setattr(auth_methods, "get_user", get_wrong_tenant_user)

    with pytest.raises(HTTPException) as exc_info:
        await auth_methods.get_current_user(_request(), _SessionDatabase(_session()))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"
