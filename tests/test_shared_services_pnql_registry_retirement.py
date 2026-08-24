"""Source-contract regression for retired unscoped shared PNQL execution wiring."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_SERVICES = ROOT / "backend_api/shared/services.py"
TELEMETRY_ROUTE = ROOT / "backend_api/routes/telemetry.py"


def test_shared_services_keeps_only_the_active_telemetry_accessor_boundary():
    source = SHARED_SERVICES.read_text(encoding="utf-8")
    telemetry_route = TELEMETRY_ROUTE.read_text(encoding="utf-8")

    assert "def get_telemetry_ingest_service" in source
    assert "from ..shared.services import get_telemetry_ingest_service" in telemetry_route
    assert "Depends(get_telemetry_ingest_service)" in telemetry_route


def test_shared_services_does_not_retain_unscoped_pnql_raw_data_or_scanner_execution():
    source = SHARED_SERVICES.read_text(encoding="utf-8")

    assert "PnqlEngine" not in source
    assert "pnql_data_sources" not in source
    assert "pnql_engine" not in source
    assert "get_logs_pnql" not in source
    assert "execute_plugins_pnql" not in source
    assert "scan_plugins" not in source
    assert "Executing scanner plugin" not in source
