"""Source-contract regressions for retired legacy log-normalizer routes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_NORMALIZER_MAIN = ROOT / "backend_api/log_normalizer/main.py"
CANONICAL_NORMALIZER_MAIN = ROOT / "backend_api/event_normalizer/main.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"
LEGACY_NORMALIZER_RETIRED_PATHS = (
    ROOT / "backend_api/log_normalizer/event_schema.py",
    ROOT / "backend_api/log_normalizer/Dockerfile",
)


def test_legacy_normalizer_has_no_schema_or_deployment_surface():
    assert all(not path.exists() for path in LEGACY_NORMALIZER_RETIRED_PATHS)
    assert "log-normalizer:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_http_log_normalizer_routes_fail_closed():
    source = LEGACY_NORMALIZER_MAIN.read_text(encoding="utf-8")

    assert 'code="LEGACY_LOG_NORMALIZER_API_RETIRED"' in source
    assert 'status_code=410' in source
    assert '@router.post("/normalize/", include_in_schema=False)' in source
    assert '@router.post("/normalize/batch", include_in_schema=False)' in source
    assert "tenant-scoped event provenance" in source
    assert "_normalize_syslog" not in source
    assert "_normalize_windows_event" not in source
    assert "except Exception:\n            continue" not in source


def test_legacy_normalizer_status_and_canonical_pipeline_are_explicit():
    legacy_source = LEGACY_NORMALIZER_MAIN.read_text(encoding="utf-8")
    canonical_source = CANONICAL_NORMALIZER_MAIN.read_text(encoding="utf-8")

    assert '"status": "legacy-log-normalizer-retired"' in legacy_source
    assert 'name="Legacy Log Normalizer Compatibility Boundary"' in legacy_source
    assert "tenant_id" in canonical_source
    assert "CONTRACT_VERSION" in canonical_source
