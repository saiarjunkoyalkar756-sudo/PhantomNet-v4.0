"""Source-contract regressions for retired simulated forensic evidence collection."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_COLLECTOR = ROOT / "backend_api/forensics_engine/evidence_collector/main.py"
FORENSICS_BOUNDARY = ROOT / "backend_api/forensics_engine/main.py"


def test_simulated_forensic_evidence_collector_remains_removed():
    assert not LEGACY_COLLECTOR.exists()


def test_forensics_engine_remains_a_fail_closed_governed_evidence_boundary():
    source = FORENSICS_BOUNDARY.read_text(encoding="utf-8")

    assert "LEGACY_FORENSICS_API_RETIRED" in source
    assert "status_code=410" in source
    assert "governed tenant-scoped evidence intake" in source
