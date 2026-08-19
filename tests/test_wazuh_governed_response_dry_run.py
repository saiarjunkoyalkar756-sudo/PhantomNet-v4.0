import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DRY_RUN = ROOT / "scripts" / "run_wazuh_governed_response_dry_run.py"
DOCKER_COMPOSE = ROOT / "docker-compose.wazuh-governed-dry-run.yml"
DOCKER_RUNNER = ROOT / "scripts" / "run_docker_wazuh_governed_response_dry_run.sh"


def test_isolated_operational_dry_run_exercises_approved_wazuh_lifecycle(tmp_path):
    environment = {
        **os.environ,
        "PHANTOMNET_WAZUH_DRY_RUN_ARTIFACT_DIR": str(tmp_path),
    }
    completed = subprocess.run(
        [sys.executable, str(DRY_RUN)],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    summary = json.loads(completed.stdout)
    artifacts = list(tmp_path.glob("wazuh_governed_response_dry_run_*.json"))
    assert summary["status"] == "passed"
    assert summary["audit_chain_valid"] is True
    assert len(artifacts) == 1
    evidence = json.loads(artifacts[0].read_text(encoding="utf-8"))
    assert evidence["scope"] == "isolated_sqlite_simulated_wazuh_no_network_no_endpoint_change"
    telemetry = evidence["telemetry_evidence"]
    assert telemetry["forwarder_id"]
    assert telemetry == {
        "forwarder_id": telemetry["forwarder_id"],
        "batch_id": "dry-run-wazuh-batch-001",
        "sequence": 1,
        "asset_created": 1,
        "integrity_created": 1,
        "canonical_event_count": 2,
        "adapter_mode": "read_only_streaming",
        "automatic_enforcement": False,
    }
    assert evidence["execution_status"] == "verified"
    assert evidence["rollback_status"] == "rolled_back"
    assert evidence["wazuh_commands"] == ["!phantomnet-network-isolate", "!phantomnet-network-release"]
    assert len(evidence["receipt_ids"]) == 2
    assert evidence["audit_record_count"] == 4
    assert evidence["safety"] == {
        "automatic_enforcement": False,
        "endpoint_actions": False,
        "external_wazuh": False,
        "network_calls": False,
    }


def test_docker_dry_run_manifest_and_runner_remain_disposable_and_internal_only():
    compose = DOCKER_COMPOSE.read_text(encoding="utf-8")
    runner = DOCKER_RUNNER.read_text(encoding="utf-8")

    assert "run_wazuh_governed_response_dry_run.py" in compose
    assert "read_only: true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "internal: true" in compose
    assert "ports:" not in compose
    assert "PHANTOMNET_WAZUH_RESPONSE_ENABLED" not in compose
    assert "docker compose version" in runner
    assert "--abort-on-container-exit" in runner
    assert "--exit-code-from governed-response-dry-run" in runner
    assert "down --volumes --remove-orphans" in runner
    assert "no_network_no_endpoint_change" in runner
    assert "production" in runner.lower()
