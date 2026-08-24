"""Tenant-boundary regressions for the active alert-storage broker consumer."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest

from backend_api.alert_storage.tenant import require_alert_tenant_id


ROOT = Path(__file__).resolve().parents[1]
ALERT_STORAGE_MAIN = ROOT / "backend_api/alert_storage/main.py"
ALERT_STORAGE_TENANT = ROOT / "backend_api/alert_storage/tenant.py"


TENANT_ID = "00000000-0000-0000-0000-000000000001"


def test_alert_storage_accepts_only_an_explicit_valid_tenant_identifier():
    assert require_alert_tenant_id({"tenant_id": TENANT_ID}) == UUID(TENANT_ID)


@pytest.mark.parametrize(
    "alert",
    [
        {},
        {"tenant_id": ""},
        {"tenant_id": "not-a-uuid"},
        {"tenant_id": 7},
        [],
    ],
)
def test_alert_storage_rejects_broker_records_without_a_valid_tenant_identifier(alert):
    with pytest.raises(ValueError):
        require_alert_tenant_id(alert)


def test_alert_storage_source_has_no_shared_default_tenant_fallback():
    main_source = ALERT_STORAGE_MAIN.read_text(encoding="utf-8")
    tenant_source = ALERT_STORAGE_TENANT.read_text(encoding="utf-8")
    assert "DEFAULT_TENANT_ID" not in main_source
    assert "from .tenant import require_alert_tenant_id" in main_source
    assert "require_alert_tenant_id(alert)" in main_source
    assert "Alert broker record is missing tenant_id" in tenant_source
