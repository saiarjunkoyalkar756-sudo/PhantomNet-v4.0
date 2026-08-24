"""Source-contract regressions for retired legacy log-service retrieval."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_API = ROOT / "backend_api/log_service/api.py"
LOG_MAIN = ROOT / "backend_api/log_service/main.py"
RAW_LOG_ROUTE = ROOT / "backend_api/routes/logs.py"


def test_unmounted_raw_log_route_remains_retired():
    assert not RAW_LOG_ROUTE.exists()


def test_legacy_log_retrieval_routes_fail_closed_without_raw_data_access():
    source = LOG_API.read_text(encoding="utf-8")

    assert 'code="LEGACY_LOG_RETRIEVAL_API_RETIRED"' in source
    assert 'status_code=410' in source
    assert '@router.get("/logs", include_in_schema=False)' in source
    assert '@router.get("/logs/poll", include_in_schema=False)' in source
    assert "tenant-scoped" in source
    assert "AttackLog" not in source
    assert "RawLogEvent" not in source
    assert "get_raw_log_events" not in source
    assert "db.query" not in source


def test_log_service_status_does_not_claim_legacy_retrieval_is_operational():
    source = LOG_MAIN.read_text(encoding="utf-8")

    assert '"status": "legacy-log-retrieval-retired"' in source
    assert "governed tenant-scoped evidence integration" in source
    assert "log-service-operational" not in source
