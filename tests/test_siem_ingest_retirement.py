"""Source-contract regressions for retired legacy SIEM ingestion routes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIEM_MAIN = ROOT / "backend_api/siem_ingest_service/main.py"
ENDPOINT_INVENTORY_MAIN = ROOT / "backend_api/endpoint_inventory_service/main.py"


def test_legacy_siem_ingest_and_raw_read_routes_fail_closed():
    source = SIEM_MAIN.read_text(encoding="utf-8")

    assert 'code="LEGACY_SIEM_INGEST_API_RETIRED"' in source
    assert 'status_code=410' in source
    assert '@router.post("/ingest/", include_in_schema=False)' in source
    assert '@router.post("/ingest/batch", include_in_schema=False)' in source
    assert '@router.get("/logs/{log_id}", include_in_schema=False)' in source
    assert '@router.get("/logs/", include_in_schema=False)' in source
    assert "tenant-scoped evidence provenance" in source
    assert "create_raw_log_event" not in source
    assert "get_raw_log_event" not in source
    assert "get_raw_log_events" not in source


def test_legacy_siem_status_and_governed_telemetry_boundary_are_explicit():
    legacy_source = SIEM_MAIN.read_text(encoding="utf-8")
    governed_source = ENDPOINT_INVENTORY_MAIN.read_text(encoding="utf-8")

    assert '"status": "legacy-siem-ingest-retired"' in legacy_source
    assert 'name="Legacy SIEM Compatibility Boundary"' in legacy_source
    assert '@app.post("/wazuh/alerts", status_code=201)' in governed_source
    assert 'require_capability("config:write")' in governed_source
    assert "current_user.tenant_id" in governed_source
