"""Source-contract regressions for the retired fixture-backed Kafka enrichment service."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENRICHMENT_SERVICE_DIR = ROOT / "backend_api/enrichment_service"
THREAT_INTELLIGENCE_MAIN = ROOT / "backend_api/threat_intelligence_service/main.py"


def test_fixture_backed_kafka_enrichment_service_and_container_surface_remain_absent():
    assert not ENRICHMENT_SERVICE_DIR.exists()
    assert not (ENRICHMENT_SERVICE_DIR / "app.py").exists()
    assert not (ENRICHMENT_SERVICE_DIR / "Dockerfile").exists()
    assert not (ENRICHMENT_SERVICE_DIR / "requirements.txt").exists()


def test_bounded_capability_protected_threat_intelligence_advisory_api_remains_distinct():
    source = THREAT_INTELLIGENCE_MAIN.read_text(encoding="utf-8")

    assert '@router.post("/threat-intel/lookup")' in source
    assert '@router.post("/threat-intel/bulk")' in source
    assert 'require_capability("alerts:read")' in source
    assert "MAX_BULK_LOOKUPS = 50" in source
    assert "_safe_enrichment_view" in source
