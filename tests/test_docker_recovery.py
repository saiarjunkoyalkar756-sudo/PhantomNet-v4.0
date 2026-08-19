"""Docker-only recovery validation for isolated non-production dependencies."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_docker_recovery_validation.sh"


def _require_docker_validation() -> None:
    if os.getenv("PHANTOMNET_DOCKER_AVAILABLE", "").lower() != "true":
        pytest.skip("Docker required: set PHANTOMNET_DOCKER_AVAILABLE=true")
    if shutil.which("docker") is None:
        pytest.skip("Docker required: Docker executable not found")
    compose_version = subprocess.run(
        ["docker", "compose", "version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if compose_version.returncode != 0:
        pytest.skip("Docker required: Docker Compose v2 is unavailable")


def _load_evidence(artifact_dir: Path) -> list[dict[str, object]]:
    evidence_files = sorted(artifact_dir.glob("docker_recovery_validation_*.jsonl"))
    assert len(evidence_files) == 1
    return [json.loads(line) for line in evidence_files[0].read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.mark.docker
def test_broker_and_postgres_restart_recovery_preserves_signed_audit_evidence(tmp_path: Path):
    """Run the production-like isolated Compose recovery harness only when Docker is explicitly enabled."""
    _require_docker_validation()
    environment = os.environ | {
        "RECOVERY_DB_PASSWORD": secrets.token_urlsafe(32),
        "RECOVERY_AUDIT_HMAC_KEY": secrets.token_urlsafe(48),
        "RECOVERY_AUDIT_HMAC_KEY_ID": f"recovery-test-key-{secrets.token_hex(8)}",
        "PHANTOMNET_RECOVERY_ARTIFACT_DIR": str(tmp_path),
    }
    completed = subprocess.run(
        ["bash", str(RUNNER)],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr

    evidence = _load_evidence(tmp_path)
    passed_checks = {(entry.get("check"), entry.get("status")) for entry in evidence}
    assert ("broker_round_trip", "passed") in passed_checks
    assert ("postgres_write_read", "passed") in passed_checks
    assert ("audit_chain_integrity", "passed") in passed_checks
    assert ("broker_outage_fail_closed", "passed") in passed_checks
    assert ("postgres_outage_fail_closed", "passed") in passed_checks
    assert {entry.get("phase") for entry in evidence if entry.get("status") == "started"} == {
        "startup",
        "broker_restart",
        "postgres_restart",
    }
    assert evidence[-1] == {"phase": "complete", "status": "passed"}

    audit_record_counts = [
        int(entry["record_count"])
        for entry in evidence
        if entry.get("check") == "audit_chain_integrity" and entry.get("status") == "passed"
    ]
    assert audit_record_counts == [1, 2, 3, 4, 5, 6]
