"""Source-contract regressions for retired unmounted external IP-information routes."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IP_INFO_SERVICE = ROOT / "backend_api/ip_info_service"
LEGACY_IP_INFO_ROUTE = ROOT / "backend_api/routes/ip_info.py"
THREAT_INTELLIGENCE_MAIN = ROOT / "backend_api/threat_intelligence_service/main.py"


def test_unmounted_duplicate_external_ip_information_modules_remain_absent():
    assert not IP_INFO_SERVICE.exists()
    assert not (IP_INFO_SERVICE / "main.py").exists()
    assert not (IP_INFO_SERVICE / "api.py").exists()
    assert not LEGACY_IP_INFO_ROUTE.exists()


def test_bounded_capability_protected_threat_intelligence_advisory_boundary_remains_distinct():
    source = THREAT_INTELLIGENCE_MAIN.read_text(encoding="utf-8")

    assert '@router.post("/threat-intel/lookup")' in source
    assert '@router.post("/threat-intel/bulk")' in source
    assert 'require_capability("alerts:read")' in source
    assert "MAX_BULK_LOOKUPS = 50" in source
    assert "_safe_enrichment_view" in source
