"""Secret-safe runtime security posture assessment for PhantomNet services.

This module reports only control states and configuration identifiers. It never returns an
environment secret, connection string, endpoint credential, or HMAC material.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any


STRICT_ENVIRONMENTS = {"production", "staging"}


def _enabled(environment: Mapping[str, str], key: str) -> bool:
    return environment.get(key, "false").strip().lower() in {"1", "true", "yes", "on"}


def _csv(environment: Mapping[str, str], key: str) -> set[str]:
    return {value.strip() for value in environment.get(key, "").split(",") if value.strip()}


def _control(status: str, reason: str, **details: Any) -> dict[str, Any]:
    return {"status": status, "reason": reason, **details}


def _wazuh_allowlist_state(environment: Mapping[str, str]) -> tuple[bool, str | None, int]:
    raw = environment.get("PHANTOMNET_WAZUH_RESPONSE_TENANT_AGENT_ALLOWLIST", "{}")
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError:
        return False, "invalid_tenant_agent_allowlist_json", 0
    if not isinstance(mapping, dict) or any(
        not isinstance(tenant_id, str)
        or not isinstance(agent_ids, list)
        or not all(isinstance(agent_id, str) and agent_id.isdigit() and 3 <= len(agent_id) <= 16 for agent_id in agent_ids)
        for tenant_id, agent_ids in mapping.items()
    ):
        return False, "invalid_tenant_agent_allowlist_shape", 0
    return True, None, len(mapping)


def _aws_allowlist_state(environment: Mapping[str, str]) -> tuple[bool, str | None, int]:
    raw = environment.get("PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST", "{}")
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError:
        return False, "invalid_tenant_security_group_allowlist_json", 0
    if not isinstance(mapping, dict) or any(
        not isinstance(tenant_id, str)
        or not isinstance(group_ids, list)
        or not all(isinstance(group_id, str) for group_id in group_ids)
        for tenant_id, group_ids in mapping.items()
    ):
        return False, "invalid_tenant_security_group_allowlist_shape", 0
    return True, None, len(mapping)


def assess_runtime_posture(
    *,
    safe_mode: bool,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return non-secret configuration posture used by readiness checks and operators.

    A disabled adapter is an intentional state. An enabled response adapter that lacks its
    approval-audit material or a required allowlist is not ready and causes active readiness
    to fail closed.
    """

    values = environment or os.environ
    deployment_environment = values.get("ENVIRONMENT", "development").strip().lower()
    hmac_ready = bool(values.get("PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY")) and bool(
        values.get("PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID")
    )
    controls: dict[str, dict[str, Any]] = {
        "safe_mode": _control(
            "enabled" if safe_mode else "disabled",
            "real_integrations_disabled" if safe_mode else "operator_enabled_active_mode",
        ),
        "containment_audit": _control(
            "ready" if hmac_ready else "degraded",
            "hmac_execution_audit_configured" if hmac_ready else "hmac_execution_audit_not_configured",
        ),
    }

    endpoint_enabled = _enabled(values, "PHANTOMNET_ENDPOINT_CONTAINMENT_ENABLED")
    endpoint_tenants = _csv(values, "PHANTOMNET_ENDPOINT_CONTAINMENT_ALLOWED_TENANTS")
    endpoint_assets = _csv(values, "PHANTOMNET_ENDPOINT_CONTAINMENT_ALLOWED_ASSETS")
    if not endpoint_enabled:
        controls["endpoint_containment"] = _control("disabled", "adapter_disabled_by_default")
    elif not hmac_ready:
        controls["endpoint_containment"] = _control("not_ready", "missing_hmac_execution_audit")
    elif not endpoint_tenants or not endpoint_assets:
        controls["endpoint_containment"] = _control("not_ready", "missing_tenant_or_asset_allowlist")
    else:
        controls["endpoint_containment"] = _control(
            "ready",
            "explicitly_enabled_with_allowlists",
            allowed_tenant_count=len(endpoint_tenants),
            allowed_asset_count=len(endpoint_assets),
        )

    aws_enabled = _enabled(values, "PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED")
    aws_regions = _csv(values, "PHANTOMNET_AWS_ALLOWED_REGIONS")
    aws_accounts = _csv(values, "PHANTOMNET_AWS_ALLOWED_ACCOUNT_IDS")
    aws_cidrs = _csv(values, "PHANTOMNET_AWS_ALLOWED_CIDRS")
    aws_allowlist_valid, aws_allowlist_error, aws_tenant_count = _aws_allowlist_state(values)
    aws_endpoint_override = values.get("PHANTOMNET_AWS_ENDPOINT_URL", "").strip()
    if not aws_enabled:
        controls["aws_security_group_containment"] = _control("disabled", "adapter_disabled_by_default")
    elif not aws_allowlist_valid:
        controls["aws_security_group_containment"] = _control("not_ready", aws_allowlist_error or "invalid_allowlist")
    elif not hmac_ready:
        controls["aws_security_group_containment"] = _control("not_ready", "missing_hmac_execution_audit")
    elif deployment_environment in STRICT_ENVIRONMENTS and aws_endpoint_override:
        controls["aws_security_group_containment"] = _control("not_ready", "test_endpoint_override_forbidden_in_strict_environment")
    elif not aws_regions or not aws_accounts or not aws_cidrs or not aws_tenant_count:
        controls["aws_security_group_containment"] = _control("not_ready", "missing_cloud_allowlist")
    else:
        controls["aws_security_group_containment"] = _control(
            "ready",
            "explicitly_enabled_with_scoped_allowlists",
            allowed_region_count=len(aws_regions),
            allowed_account_count=len(aws_accounts),
            allowed_cidr_count=len(aws_cidrs),
            allowed_tenant_count=aws_tenant_count,
            endpoint_override_configured=bool(aws_endpoint_override),
        )

    wazuh_enabled = _enabled(values, "PHANTOMNET_WAZUH_RESPONSE_ENABLED")
    wazuh_url = values.get("PHANTOMNET_WAZUH_RESPONSE_API_BASE_URL", "").strip()
    wazuh_profiles = _csv(values, "PHANTOMNET_WAZUH_RESPONSE_ALLOWED_PROFILES")
    wazuh_allowlist_valid, wazuh_allowlist_error, wazuh_tenant_count = _wazuh_allowlist_state(values)
    wazuh_credentials_configured = bool(values.get("PHANTOMNET_WAZUH_RESPONSE_API_USERNAME")) and bool(
        values.get("PHANTOMNET_WAZUH_RESPONSE_API_PASSWORD")
    )
    wazuh_command_key_configured = bool(values.get("PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY")) and bool(
        values.get("PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY_ID")
    )
    wazuh_insecure_lab = _enabled(values, "PHANTOMNET_WAZUH_RESPONSE_ALLOW_INSECURE_HTTP")
    if not wazuh_enabled:
        controls["wazuh_active_response"] = _control("disabled", "adapter_disabled_by_default")
    elif not hmac_ready:
        controls["wazuh_active_response"] = _control("not_ready", "missing_hmac_execution_audit")
    elif not wazuh_allowlist_valid:
        controls["wazuh_active_response"] = _control("not_ready", wazuh_allowlist_error or "invalid_tenant_agent_allowlist")
    elif not wazuh_url or not (wazuh_url.startswith("https://") or wazuh_url.startswith("http://")):
        controls["wazuh_active_response"] = _control("not_ready", "missing_or_invalid_api_base_url")
    elif wazuh_url.startswith("http://") and (deployment_environment in STRICT_ENVIRONMENTS or not wazuh_insecure_lab):
        controls["wazuh_active_response"] = _control("not_ready", "https_required_outside_explicit_isolated_lab")
    elif not wazuh_credentials_configured or not wazuh_command_key_configured:
        controls["wazuh_active_response"] = _control("not_ready", "missing_wazuh_credentials_or_command_hmac")
    elif not wazuh_tenant_count or not wazuh_profiles:
        controls["wazuh_active_response"] = _control("not_ready", "missing_tenant_agent_or_profile_allowlist")
    else:
        controls["wazuh_active_response"] = _control(
            "ready" if wazuh_url.startswith("https://") else "degraded",
            "https_command_transport_configured" if wazuh_url.startswith("https://") else "isolated_lab_http_explicitly_enabled",
            allowed_tenant_count=wazuh_tenant_count,
            allowed_profile_count=len(wazuh_profiles),
            transport="https" if wazuh_url.startswith("https://") else "http",
        )

    replication_enabled = _enabled(values, "PHANTOMNET_TELEMETRY_REPLICATION_ENABLED")
    replication_brokers = values.get("PHANTOMNET_REPLICATION_KAFKA_BOOTSTRAP_SERVERS", "").strip()
    replication_protocol = values.get("PHANTOMNET_REPLICATION_KAFKA_SECURITY_PROTOCOL", "SSL").strip().upper()
    replication_mtls_configured = all(
        values.get(key, "").strip()
        for key in (
            "PHANTOMNET_REPLICATION_KAFKA_SSL_CAFILE",
            "PHANTOMNET_REPLICATION_KAFKA_SSL_CERTFILE",
            "PHANTOMNET_REPLICATION_KAFKA_SSL_KEYFILE",
        )
    )
    if not replication_enabled:
        controls["telemetry_replication"] = _control("disabled", "transport_disabled_by_default")
    elif not replication_brokers:
        controls["telemetry_replication"] = _control("not_ready", "missing_regional_broker_configuration")
    elif deployment_environment in STRICT_ENVIRONMENTS and replication_protocol != "SSL":
        controls["telemetry_replication"] = _control("not_ready", "tls_required_in_strict_environment")
    else:
        controls["telemetry_replication"] = _control(
            "ready" if replication_protocol == "SSL" else "degraded",
            "secured_transport_configured" if replication_protocol == "SSL" else "non_tls_transport_configured",
            security_protocol=replication_protocol,
            mtls_configured=replication_mtls_configured,
        )

    graph_backend = values.get("PHANTOMNET_GRAPH_BACKEND", "memory").strip().lower()
    if graph_backend not in {"memory", "neo4j"}:
        controls["graph_backend"] = _control("not_ready", "unsupported_graph_backend")
    elif graph_backend == "neo4j" and not values.get("NEO4J_PASSWORD"):
        controls["graph_backend"] = _control("not_ready", "missing_neo4j_password", backend=graph_backend)
    else:
        controls["graph_backend"] = _control(
            "ready" if graph_backend == "neo4j" else "degraded",
            "durable_backend_configured" if graph_backend == "neo4j" else "ephemeral_memory_backend",
            backend=graph_backend,
        )

    blocking_controls = sorted(
        name for name, control in controls.items() if control["status"] == "not_ready"
    )
    return {
        "status": "not_ready" if blocking_controls else "ready",
        "environment": deployment_environment,
        "safe_mode": safe_mode,
        "blocking_controls": blocking_controls,
        "controls": controls,
    }
