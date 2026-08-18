import pytest

from backend_api.shared import health
from backend_api.shared.runtime_posture import assess_runtime_posture
from backend_api.shared.settings import Settings


TENANT_ID = "00000000-0000-0000-0000-000000000001"
SECURITY_GROUP_ID = "sg-0123456789abcdef0"


def _aws_environment(**overrides):
    values = {
        "ENVIRONMENT": "development",
        "PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY": "runtime-posture-test-hmac",
        "PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID": "runtime-posture-test-key",
        "PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED": "true",
        "PHANTOMNET_AWS_ALLOWED_REGIONS": "us-east-1",
        "PHANTOMNET_AWS_ALLOWED_ACCOUNT_IDS": "123456789012",
        "PHANTOMNET_AWS_ALLOWED_CIDRS": "203.0.113.0/24",
        "PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST": f'{{"{TENANT_ID}":["{SECURITY_GROUP_ID}"]}}',
        "PHANTOMNET_GRAPH_BACKEND": "memory",
    }
    values.update(overrides)
    return values


def test_runtime_posture_reports_disabled_response_adapters_without_exposing_secret_values():
    posture = assess_runtime_posture(safe_mode=True, environment={})

    assert posture["status"] == "ready"
    assert posture["safe_mode"] is True
    assert posture["controls"]["endpoint_containment"] == {
        "status": "disabled",
        "reason": "adapter_disabled_by_default",
    }
    assert posture["controls"]["aws_security_group_containment"] == {
        "status": "disabled",
        "reason": "adapter_disabled_by_default",
    }
    assert "HMAC" not in repr(posture)


def test_runtime_posture_fails_closed_for_enabled_aws_adapter_without_signed_audit_material():
    environment = _aws_environment(
        PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY="",
        PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID="",
    )

    posture = assess_runtime_posture(safe_mode=False, environment=environment)

    assert posture["status"] == "not_ready"
    assert posture["controls"]["aws_security_group_containment"] == {
        "status": "not_ready",
        "reason": "missing_hmac_execution_audit",
    }
    assert "aws_security_group_containment" in posture["blocking_controls"]


def test_runtime_posture_rejects_localstack_override_in_strict_environment_and_invalid_allowlists():
    strict = assess_runtime_posture(
        safe_mode=False,
        environment=_aws_environment(
            ENVIRONMENT="production",
            PHANTOMNET_AWS_ENDPOINT_URL="http://localstack:4566",
        ),
    )
    assert strict["controls"]["aws_security_group_containment"] == {
        "status": "not_ready",
        "reason": "test_endpoint_override_forbidden_in_strict_environment",
    }

    invalid = assess_runtime_posture(
        safe_mode=False,
        environment=_aws_environment(PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST="[]"),
    )
    assert invalid["controls"]["aws_security_group_containment"] == {
        "status": "not_ready",
        "reason": "invalid_tenant_security_group_allowlist_shape",
    }


def test_runtime_posture_reports_ready_scoped_aws_controls_without_secret_material():
    posture = assess_runtime_posture(safe_mode=False, environment=_aws_environment())

    aws = posture["controls"]["aws_security_group_containment"]
    assert posture["status"] == "ready"
    assert aws["status"] == "ready"
    assert aws["allowed_region_count"] == 1
    assert aws["allowed_account_count"] == 1
    assert aws["allowed_cidr_count"] == 1
    assert aws["allowed_tenant_count"] == 1
    assert aws["endpoint_override_configured"] is False
    assert "runtime-posture-test-hmac" not in repr(posture)


def test_typed_settings_prefers_canonical_safe_mode_environment_name(monkeypatch):
    monkeypatch.setenv("PHANTOMNET_SAFE_MODE", "false")
    monkeypatch.delenv("SAFE_MODE", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "runtime-posture-test-jwt-secret-at-least-32-characters")

    settings = Settings(_env_file=None)

    assert settings.SAFE_MODE is False


@pytest.mark.asyncio
async def test_active_readiness_fails_closed_when_security_posture_has_blocking_control(monkeypatch):
    async def healthy_component():
        return {"status": "healthy"}

    monkeypatch.setattr(health, "SAFE_MODE", False)
    monkeypatch.setitem(health.HEALTH_CHECKS, "database", healthy_component)
    monkeypatch.setattr(
        health,
        "assess_runtime_posture",
        lambda *, safe_mode: {
            "status": "not_ready",
            "environment": "production",
            "safe_mode": safe_mode,
            "blocking_controls": ["aws_security_group_containment"],
            "controls": {"aws_security_group_containment": {"status": "not_ready", "reason": "missing_hmac_execution_audit"}},
        },
    )

    result = await health.run_standard_health_check(required_dependencies=("database",))

    assert result["readiness"] == "not_ready"
    assert result["status"] == "degraded"
    assert result["security_posture"]["blocking_controls"] == ["aws_security_group_containment"]
