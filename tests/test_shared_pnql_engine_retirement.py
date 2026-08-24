"""Source-contract regression for retired shared PNQL simulation engine."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_PNQL = ROOT / "backend_api/shared/pnql_engine.py"
SHARED_PNQL_TEST = ROOT / "backend_api/shared/test_pnql_engine.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
LEGACY_PHANTOMQL = ROOT / "backend_api/phantomql_engine/main.py"
THREAT_HUNTING_MAIN = ROOT / "backend_api/threat_hunting_service/main.py"


def test_shared_pnql_engine_and_obsolete_unit_tests_remain_absent():
    assert not SHARED_PNQL.exists()
    assert not SHARED_PNQL_TEST.exists()
    assert "shared.pnql_engine" not in GATEWAY_MAIN.read_text(encoding="utf-8")


def test_fail_closed_phantomql_and_governed_threat_hunting_remain_separate():
    assert "LEGACY_PHANTOMQL_API_RETIRED" in LEGACY_PHANTOMQL.read_text(encoding="utf-8")
    assert "ThreatHuntingService" in THREAT_HUNTING_MAIN.read_text(encoding="utf-8")
