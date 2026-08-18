"""Central role-to-capability policy used by PhantomNet operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, FrozenSet

from fastapi import Depends, HTTPException, status

from backend_api.iam_service.auth_methods import get_current_user


ROLE_CAPABILITIES: dict[str, FrozenSet[str]] = {
    "viewer": frozenset({"alerts:read", "audit:read"}),
    "analyst": frozenset(
        {
            "alerts:read",
            "audit:read",
            "cases:write",
            "response:request",
            "rules:read",
            "agents:command",
        }
    ),
    "admin": frozenset(
        {
            "alerts:read",
            "audit:read",
            "cases:write",
            "response:request",
            "response:approve",
            "rules:write",
            "config:write",
            "agents:bootstrap",
            "agents:approve",
            "agents:command",
            "blacklist:write",
            "users:read",
        }
    ),
}


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    role: str
    capability: str
    reason: str


def _normalized_role(role: str | Enum) -> str:
    value = role.value if isinstance(role, Enum) else role
    return str(value).strip().lower()


def authorize(role: str | Enum, capability: str) -> AuthorizationDecision:
    normalized_role = _normalized_role(role)
    capabilities = ROLE_CAPABILITIES.get(normalized_role, frozenset())
    allowed = capability in capabilities
    return AuthorizationDecision(
        allowed=allowed,
        role=normalized_role,
        capability=capability,
        reason="capability granted" if allowed else "role is not authorized for this capability",
    )


def require_authorized(role: str | Enum, capability: str) -> None:
    decision = authorize(role, capability)
    if not decision.allowed:
        raise PermissionError(f"{decision.role} cannot perform {decision.capability}: {decision.reason}")


def require_capability(capability: str):
    """Return a FastAPI dependency that enforces one central RBAC capability.

    Authentication remains the responsibility of ``get_current_user``. The dependency
    returns the authenticated user after making a policy-based authorization decision.
    """

    async def capability_checker(current_user: Any = Depends(get_current_user)) -> Any:
        try:
            require_authorized(getattr(current_user, "role", ""), capability)
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        return current_user

    return capability_checker
