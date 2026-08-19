from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_docker_topology_validation.sh"
COMPOSE_FILE = ROOT / "docker-compose.integration.yml"


def test_docker_topology_validation_runner_is_nonproduction_health_gated_and_disposable():
    script = RUNNER.read_text(encoding="utf-8")

    assert "Docker Engine is required for topology validation." in script
    assert "Docker Compose v2 is required for topology validation." in script
    assert "--profile verify" in script
    assert "--abort-on-container-exit --exit-code-from integration-tests" in script
    assert "compose down --volumes --remove-orphans" in script
    assert "trap cleanup EXIT" in script
    assert "phantomnet-topology-" in script
    assert str(COMPOSE_FILE) not in script
    assert "docker-compose.integration.yml" in script


def test_docker_topology_validation_compose_uses_only_the_dedicated_live_topology_test():
    compose = COMPOSE_FILE.read_text(encoding="utf-8")

    assert "infra/docker/integration-test.Dockerfile" in compose
    assert "tests/test_live_integration_topology.py" in compose
    assert "PHANTOMNET_INTEGRATION: \"1\"" in compose
    assert "condition: service_healthy" in compose
