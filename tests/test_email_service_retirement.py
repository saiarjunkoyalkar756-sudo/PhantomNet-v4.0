"""Source-contract regression for retired simulated password-reset email logger."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EMAIL_SERVICE = ROOT / "backend_api/shared/email_service.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
PASSWORD_RESET_API = ROOT / "backend_api/iam_service/api.py"


def test_simulated_email_logger_and_gateway_import_remain_absent():
    assert not EMAIL_SERVICE.exists()
    source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "email_service" not in source
    assert "send_reset_email" not in source


def test_password_reset_boundary_remains_separate_and_fail_closed():
    source = PASSWORD_RESET_API.read_text(encoding="utf-8")
    assert "LEGACY_SIMULATED_PASSWORD_RESET_RETIRED" in source
    assert "status_code=410" in source
