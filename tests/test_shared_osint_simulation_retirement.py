"""Source-contract regression for retired randomized shared OSINT simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OSINT_ENGINE = ROOT / "backend_api/shared/osint_engine.py"
SHARED_SERVICES = ROOT / "backend_api/shared/services.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
THREAT_INTEL_MAIN = ROOT / "backend_api/threat_intelligence_service/main.py"


def test_randomized_shared_osint_simulation_and_unused_imports_remain_absent():
    assert not OSINT_ENGINE.exists()

    shared_services = SHARED_SERVICES.read_text(encoding="utf-8")
    gateway = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "osint_engine" not in shared_services
    assert "OsintEngine" not in gateway
    assert "shared.osint_engine" not in gateway


def test_governed_threat_intelligence_and_canonical_telemetry_paths_remain_separate():
    threat_intel = THREAT_INTEL_MAIN.read_text(encoding="utf-8")
    shared_services = SHARED_SERVICES.read_text(encoding="utf-8")

    assert "Legacy Threat Intelligence API" not in threat_intel
    assert "get_telemetry_ingest_service" in shared_services
