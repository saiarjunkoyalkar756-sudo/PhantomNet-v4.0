"""Source-contract regression for retired simulated threat marketplace."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THREAT_MARKETPLACE = ROOT / "features/ai_threat_marketplace"
THREAT_INTELLIGENCE_MAIN = ROOT / "backend_api/threat_intelligence_service/main.py"
WORLD_INTEL_ADAPTER = ROOT / "backend_api/threat_intelligence_service/world_intel_adapter.py"


def test_simulated_threat_marketplace_package_remains_absent():
    assert not THREAT_MARKETPLACE.exists()


def test_advisory_threat_intelligence_boundary_remains_capability_protected():
    main_source = THREAT_INTELLIGENCE_MAIN.read_text(encoding="utf-8")
    adapter_source = WORLD_INTEL_ADAPTER.read_text(encoding="utf-8")

    assert 'require_capability("alerts:read")' in main_source
    assert "Capability-protected advisory indicator enrichment" in main_source
    assert '"automatic_enforcement": False' in adapter_source
