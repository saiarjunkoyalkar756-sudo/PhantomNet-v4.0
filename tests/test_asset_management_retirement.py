"""Source-contract regression for retired simulated asset-management module."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMULATED_ASSET_MANAGEMENT = ROOT / "backend_api/shared/asset_management.py"
SIMULATED_ASSET_MANAGEMENT_TEST = ROOT / "backend_api/shared/test_asset_management.py"
ENDPOINT_INVENTORY_MAIN = ROOT / "backend_api/endpoint_inventory_service/main.py"
ENDPOINT_INVENTORY_INGESTION = ROOT / "backend_api/endpoint_inventory_service/ingestion.py"


def test_simulated_asset_management_module_remains_absent():
    assert not SIMULATED_ASSET_MANAGEMENT.exists()
    assert not SIMULATED_ASSET_MANAGEMENT_TEST.exists()


def test_governed_endpoint_inventory_boundary_remains_present():
    main_source = ENDPOINT_INVENTORY_MAIN.read_text(encoding="utf-8")
    ingestion_source = ENDPOINT_INVENTORY_INGESTION.read_text(encoding="utf-8")

    assert '@app.post("/assets", status_code=201)' in main_source
    assert "current_user.tenant_id" in main_source
    assert "EndpointTelemetryIngestion" in ingestion_source
    assert "tenant_id" in ingestion_source
