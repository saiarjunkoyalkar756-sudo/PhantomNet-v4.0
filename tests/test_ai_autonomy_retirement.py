"""Source-contract regression for retired unmounted AI-autonomy surface."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTONOMY_ROUTER = ROOT / "backend_api/routes/ai_autonomy.py"
AUTONOMY_PACKAGE = ROOT / "features/ai_autonomy_levels"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_unmounted_ai_autonomy_router_and_package_remain_absent():
    assert not AUTONOMY_ROUTER.exists()
    assert not AUTONOMY_PACKAGE.exists()


def test_governed_containment_remains_human_approval_and_rollback_bound():
    source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")

    assert "Human-governed containment lifecycle" in source
    assert "HMAC-signed audit evidence" in source
    assert "Containment rollback requires a verified execution with rollback evidence." in source
