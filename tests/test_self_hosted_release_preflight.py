"""Regression coverage for the secret-safe self-hosted release preflight."""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/preflight_self_hosted_release.sh"


def _write_env(path: Path, *, endpoint_adapter: str = "false", jwt_secret: str = "j" * 32) -> None:
    path.write_text(
        "\n".join(
            [
                "PHANTOMNET_ENVIRONMENT=staging",
                "PHANTOMNET_SAFE_MODE=false",
                "PHANTOMNET_POSTGRES_PASSWORD=postgres-password-for-test-only",
                "PHANTOMNET_REDIS_PASSWORD=redis-password-for-test-only",
                "PHANTOMNET_NEO4J_PASSWORD=neo4j-password-for-test-only",
                f"PHANTOMNET_JWT_SECRET_KEY={jwt_secret}",
                f"PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY={'h' * 32}",
                "PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID=lab-key-01",
                f"PHANTOMNET_ENDPOINT_CONTAINMENT_ENABLED={endpoint_adapter}",
                "PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED=false",
                "PHANTOMNET_WAZUH_RESPONSE_ENABLED=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _fake_docker(bin_dir: Path) -> None:
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"${1:-}\" == \"compose\" && \"${2:-}\" == \"version\" ]]; then exit 0; fi\n"
        "if [[ \"${1:-}\" == \"compose\" ]]; then exit 0; fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    docker.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def _run(env_file: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}"}
    return subprocess.run(
        [str(SCRIPT), str(env_file)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_release_preflight_accepts_protected_complete_config_without_echoing_secret_values(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_docker(bin_dir)

    result = _run(env_file, bin_dir)

    assert result.returncode == 0
    assert "Self-hosted release preflight passed." in result.stdout
    assert "postgres-password-for-test-only" not in result.stdout + result.stderr
    assert "redis-password-for-test-only" not in result.stdout + result.stderr


def test_release_preflight_rejects_enabled_response_adapter(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file, endpoint_adapter="true")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_docker(bin_dir)

    result = _run(env_file, bin_dir)

    assert result.returncode == 2
    assert "response adapters to remain disabled" in result.stderr


def test_release_preflight_rejects_insecure_environment_file_mode(tmp_path: Path):
    env_file = tmp_path / ".env"
    _write_env(env_file)
    env_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _fake_docker(bin_dir)

    result = _run(env_file, bin_dir)

    assert result.returncode == 2
    assert "readable by group or other users" in result.stderr
