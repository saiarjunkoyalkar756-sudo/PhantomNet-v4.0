"""Source-contract regressions for retired local-agent configuration disclosure routes."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_SERVICE_DIR = ROOT / "backend_api/config_service"
LEGACY_CONFIG_ROUTE = ROOT / "backend_api/routes/config.py"
ENDPOINT_INVENTORY_MAIN = ROOT / "backend_api/endpoint_inventory_service/main.py"
IAM_POLICY = ROOT / "backend_api/iam_service/policy.py"


def test_unmounted_local_agent_configuration_disclosure_modules_remain_absent():
    assert not CONFIG_SERVICE_DIR.exists()
    assert not (CONFIG_SERVICE_DIR / "main.py").exists()
    assert not (CONFIG_SERVICE_DIR / "api.py").exists()
    assert not LEGACY_CONFIG_ROUTE.exists()


def test_tenant_scoped_configuration_capability_boundary_remains_distinct():
    endpoint_inventory_source = ENDPOINT_INVENTORY_MAIN.read_text(encoding="utf-8")
    policy_source = IAM_POLICY.read_text(encoding="utf-8")

    assert 'require_capability("config:write")' in endpoint_inventory_source
    assert "current_user.tenant_id" in endpoint_inventory_source
    assert '"config:write"' in policy_source
