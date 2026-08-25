"""Source-contract regression for retired synthetic cyber-twin simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CYBER_TWIN_PACKAGE = ROOT / "features/synthetic_cyber_twin_universe"
INVENTORY_REPOSITORY = ROOT / "backend_api/endpoint_inventory_service/repository.py"


def test_synthetic_cyber_twin_simulation_package_remains_absent():
    assert not CYBER_TWIN_PACKAGE.exists()


def test_retained_endpoint_inventory_remains_tenant_scoped():
    source = INVENTORY_REPOSITORY.read_text(encoding="utf-8")

    assert "EndpointAssetRow.tenant_id == UUID(asset.tenant_id)" in source
    assert "EndpointAssetRow.tenant_id == UUID(tenant_id)" in source
