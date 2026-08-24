"""Source-contract regressions for retired simulated forensic timeline building."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_TIMELINE_BUILDER = ROOT / "backend_api/forensics_engine/timeline_builder/main.py"
FORENSICS_BOUNDARY = ROOT / "backend_api/forensics_engine/main.py"


def test_simulated_forensic_timeline_builder_remains_removed():
    assert not LEGACY_TIMELINE_BUILDER.exists()


def test_forensics_engine_remains_fail_closed_for_unscoped_timeline_requests():
    source = FORENSICS_BOUNDARY.read_text(encoding="utf-8")

    assert "LEGACY_FORENSICS_API_RETIRED" in source
    assert "status_code=410" in source
    assert "governed tenant-scoped evidence intake" in source
