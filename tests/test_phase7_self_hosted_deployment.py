from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend_api.shared import container_healthcheck
from backend_api.shared.service_factory import create_phantom_service


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deploy/self-hosted/docker-compose.yml"
PROMETHEUS = ROOT / "deploy/self-hosted/monitoring/prometheus.yml"
ENV_EXAMPLE = ROOT / "deploy/self-hosted/env/.env.example"


def test_self_hosted_compose_parses_into_the_expected_service_and_network_architecture():
    manifest = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))

    assert manifest["name"] == "phantomnet-self-hosted"
    assert {"postgres", "redis", "redpanda", "neo4j", "gateway-service", "prometheus"}.issubset(manifest["services"])
    assert manifest["networks"]["platform_internal"]["internal"] is True
    assert manifest["networks"]["observability_internal"]["internal"] is True
    assert manifest["services"]["gateway-service"]["healthcheck"]["test"][-1] == "http://127.0.0.1:8000/ready"
    assert manifest["services"]["prometheus"]["networks"] == ["observability_internal"]


def test_self_hosted_compose_uses_internal_data_networks_loopback_ingress_and_no_test_secrets():
    content = COMPOSE.read_text(encoding="utf-8")

    assert "platform_internal:\n    internal: true" in content
    assert "observability_internal:\n    internal: true" in content
    assert "127.0.0.1:${PHANTOMNET_GATEWAY_PORT:-8001}:8000" in content
    assert "127.0.0.1:${PHANTOMNET_PROMETHEUS_PORT:-9090}:9090" in content
    assert "phantomnet-test-only" not in content
    assert ":latest" not in content
    assert "PHANTOMNET_POSTGRES_PASSWORD:?" in content
    assert "PHANTOMNET_REDIS_PASSWORD:?" in content
    assert "PHANTOMNET_NEO4J_PASSWORD:?" in content
    assert "PHANTOMNET_JWT_SECRET_KEY:?" in content
    assert "PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY:?" in content
    assert "condition: service_healthy" in content
    assert "read_only: true" in content
    assert "no-new-privileges:true" in content
    assert "cap_drop:" in content


def test_phase7_observability_config_scrapes_only_the_internal_gateway_metrics_target():
    content = PROMETHEUS.read_text(encoding="utf-8")

    assert "metrics_path: /metrics" in content
    assert "gateway-service:8000" in content
    assert "scheme: http" in content
    assert "http://" not in content
    assert "https://" not in content
    assert "static_configs:" in content


def test_self_hosted_environment_template_contains_only_placeholders_and_keeps_response_adapters_disabled():
    content = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "REPLACE_WITH_" in content
    assert "phantomnet-test-only" not in content
    assert "PHANTOMNET_ENDPOINT_CONTAINMENT_ENABLED=false" in content
    assert "PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED=false" in content
    assert "PHANTOMNET_WAZUH_RESPONSE_ENABLED=false" in content


def test_container_readiness_helper_is_bounded_and_does_not_emit_transport_error_details(monkeypatch):
    class HealthyResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(container_healthcheck, "urlopen", lambda url, timeout: HealthyResponse())
    assert container_healthcheck.check("http://127.0.0.1:8000/ready", 1) == 0

    def unavailable(url, timeout):
        raise container_healthcheck.URLError("private-hostname-and-token-are-not-logged")

    monkeypatch.setattr(container_healthcheck, "urlopen", unavailable)
    assert container_healthcheck.check("http://127.0.0.1:8000/ready", 1) == 1


@pytest.mark.asyncio
async def test_standard_service_metrics_endpoint_exposes_bounded_process_counters_without_secret_or_tenant_labels():
    app = create_phantom_service("Phase7 Metrics Service", "Metrics test", version="7.0.0")
    routes = {route.path: route.endpoint for route in app.routes if hasattr(route, "endpoint")}
    response = await routes["/metrics"]()
    body = response.body.decode("utf-8")

    assert response.media_type.startswith("text/plain")
    assert 'phantomnet_http_requests_total{service="Phase7 Metrics Service"} 0' in body
    assert "phantomnet_http_requests_4xx_total" in body
    assert "phantomnet_http_requests_5xx_total" in body
    assert "phantomnet_http_request_duration_seconds_sum" in body
    assert "tenant" not in body.casefold()
    assert "secret" not in body.casefold()
