"""Tenant identity validation for direct alert-storage broker records."""

from __future__ import annotations

from typing import Any
from uuid import UUID


def require_alert_tenant_id(alert: Any) -> UUID:
    """Return a valid message tenant identifier or reject the broker record."""
    if not isinstance(alert, dict):
        raise ValueError("Alert broker record must be a JSON object")

    tenant_id = alert.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise ValueError("Alert broker record is missing tenant_id")

    try:
        return UUID(tenant_id)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Alert broker record has an invalid tenant_id") from exc
