"""Source-contract regression for retired shared simulated command dispatcher."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DISPATCHER = ROOT / "backend_api/shared/command_dispatcher.py"
LEGACY_DISPATCHER = ROOT / "backend_api/command_dispatcher/main.py"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_shared_simulated_dispatcher_remains_absent():
    assert not SHARED_DISPATCHER.exists()


def test_separate_fail_closed_dispatcher_and_governed_containment_remain():
    assert "legacy-command-dispatcher-retired" in LEGACY_DISPATCHER.read_text(encoding="utf-8")
    source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")
    assert "approval" in source.lower()
    assert "rollback" in source.lower()
