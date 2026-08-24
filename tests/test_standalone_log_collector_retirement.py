"""Source-contract regressions for the retired standalone RabbitMQ log collector."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_DIR = ROOT / "backend_api/collector"
TELEMETRY_INGESTOR_MAIN = ROOT / "backend_api/telemetry_ingestor/main.py"
ENDPOINT_INVENTORY_MAIN = ROOT / "backend_api/endpoint_inventory_service/main.py"


def test_unauthenticated_standalone_rabbitmq_collector_and_its_container_surface_remain_absent():
    assert not COLLECTOR_DIR.exists()
    assert not (COLLECTOR_DIR / "app.py").exists()
    assert not (COLLECTOR_DIR / "Dockerfile").exists()


def test_governed_telemetry_replacements_remain_distinct_from_retired_raw_log_collection():
    telemetry_source = TELEMETRY_INGESTOR_MAIN.read_text(encoding="utf-8")
    endpoint_inventory_source = ENDPOINT_INVENTORY_MAIN.read_text(encoding="utf-8")

    assert '@app.post("/ingest")' in telemetry_source
    assert "SignedTelemetryAuthService" in telemetry_source
    assert "verify_and_record" in telemetry_source
    assert "event.tenant_id" in telemetry_source
    assert '@app.post("/wazuh/alerts", status_code=201)' in endpoint_inventory_source
    assert 'require_capability("config:write")' in endpoint_inventory_source
    assert "current_user.tenant_id" in endpoint_inventory_source
