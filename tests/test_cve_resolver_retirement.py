"""Source-contract regression for retired unmounted CVE resolver prototypes."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CVE_RESOLVER_PACKAGE = ROOT / "backend_api/vulnerability_management_service/cve_resolver"
CVE_RESOLVER_SERVICE = ROOT / "backend_api/vulnerability_management_service/cve_resolver_service.py"
VULNERABILITY_MAIN = ROOT / "backend_api/vulnerability_management_service/main.py"


def test_unmounted_cve_resolver_prototypes_remain_absent():
    assert not CVE_RESOLVER_PACKAGE.exists()
    assert not CVE_RESOLVER_SERVICE.exists()


def test_retained_vulnerability_management_boundary_fails_closed():
    source = VULNERABILITY_MAIN.read_text(encoding="utf-8")
    assert "LEGACY_VULNERABILITY_API_RETIRED" in source
    assert "status_code=410" in source
