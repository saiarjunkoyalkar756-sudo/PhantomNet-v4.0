from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_recovery_compose_is_internal_only_and_health_gated():
    compose = (ROOT / "docker-compose.recovery-validation.yml").read_text(encoding="utf-8")
    assert "recovery_internal:" in compose
    assert "internal: true" in compose
    assert "redpanda:" in compose
    assert "postgres:" in compose
    assert "recovery-probe:" in compose
    assert "condition: service_healthy" in compose
    assert "ports:" not in compose
    assert "POSTGRES_PASSWORD: ${RECOVERY_DB_PASSWORD:?" in compose
    assert "RECOVERY_AUDIT_HMAC_KEY: ${RECOVERY_AUDIT_HMAC_KEY:?" in compose
    assert "RECOVERY_AUDIT_HMAC_KEY_ID: ${RECOVERY_AUDIT_HMAC_KEY_ID:?" in compose


def test_docker_recovery_runner_is_fail_fast_and_cleans_up_volumes():
    runner = (ROOT / "scripts" / "run_docker_recovery_validation.sh").read_text(encoding="utf-8")
    assert "command -v docker" in runner
    assert "docker compose version" in runner
    assert "${RECOVERY_DB_PASSWORD:?" in runner
    assert "${RECOVERY_AUDIT_HMAC_KEY:?" in runner
    assert "${RECOVERY_AUDIT_HMAC_KEY_ID:?" in runner
    assert "trap cleanup EXIT" in runner
    assert "compose down --volumes --remove-orphans" in runner
    assert "compose stop redpanda" in runner
    assert "compose start redpanda" in runner
    assert "compose stop postgres" in runner
    assert "compose start postgres" in runner
    assert "run_probe_expect_failure broker broker_outage_fail_closed" in runner
    assert "run_probe_expect_failure postgres postgres_outage_fail_closed" in runner
    assert "run_probe combined" in runner
    assert "run_probe broker" in runner
    assert "run_probe postgres" in runner
    assert runner.count("run_probe audit") == 5


def test_recovery_probe_emits_non_secret_status_evidence_without_response_adapter_use():
    probe = (ROOT / "scripts" / "run_docker_recovery_validation.py").read_text(encoding="utf-8")
    assert "broker_round_trip" in probe
    assert "postgres_write_read" in probe
    assert "audit_chain_integrity" in probe
    assert "verify_chain" in probe
    assert "response adapters" in probe
    assert "RECOVERY_POSTGRES_DSN" in probe
    assert "json.dumps(" in probe
