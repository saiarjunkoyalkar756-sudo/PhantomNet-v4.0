"""Central role-to-capability policy used by high-impact PhantomNet operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


ROLE_CAPABILITIES: dict[str, FrozenSet[str]] = {
    "viewer": frozenset({"alerts:read", "audit:read"}),
    "analyst": frozenset({"alerts:read", "audit:read", "cases:write", "response:request", "rules:read"}),
    "admin": frozenset({"alerts:read", "audit:read", "cases:write", "response:request", "response:approve", "rules:write", "config:write"}),
}


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    role: str
    capability: str
    reason: str


def authorize(role: str, capability: str) -> AuthorizationDecision:
    normalized_role = role.strip().lower()
    capabilities = ROLE_CAPABILITIES.get(normalized_role, frozenset())
    allowed = capability in capabilities
    return AuthorizationDecision(
        allowed=allowed,
        role=normalized_role,
        capability=capability,
        reason="capability granted" if allowed else "role is not authorized for this capability",
    )


def require_authorized(role: str, capability: str) -> None:
    decision = authorize(role, capability)
    if not decision.allowed:
        raise PermissionError(f"{decision.role} cannot perform {decision.capability}: {decision.reason}")
