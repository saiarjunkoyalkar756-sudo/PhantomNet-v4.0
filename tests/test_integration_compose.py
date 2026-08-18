from pathlib import Path

import yaml


COMPOSE_PATH = Path(__file__).resolve().parents[1] / "docker-compose.integration.yml"


def test_integration_compose_has_health_gated_stateful_dependencies():
    compose = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    services = compose["services"]

    for service_name in ("postgres", "redis", "redpanda", "neo4j"):
        assert service_name in services
        assert "healthcheck" in services[service_name]
        assert services[service_name]["healthcheck"]["retries"] >= 1

    runner = services["integration-tests"]
    assert runner["profiles"] == ["verify"]
    assert runner["environment"]["PHANTOMNET_INTEGRATION"] == "1"
    for dependency in ("postgres", "redis", "redpanda", "neo4j"):
        assert runner["depends_on"][dependency]["condition"] == "service_healthy"


def test_integration_compose_uses_explicit_nonproduction_credentials():
    compose = yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8"))
    postgres = compose["services"]["postgres"]
    assert postgres["environment"]["POSTGRES_DB"] == "phantomnet_test"
    assert postgres["environment"]["POSTGRES_PASSWORD"] == "phantomnet-test-only"
    assert "/var/lib/postgresql/data" in postgres["tmpfs"]
