"""Source-contract regression for retired credential-spraying simulation plugin."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KERBRUTE_PLUGIN = ROOT / "backend_api/plugins/kerbrute_scanner"
SANDBOX_RUNNER = ROOT / "backend_api/shared/sandbox_runner.py"
PLUGIN_MANAGER = ROOT / "backend_api/shared/plugin_manager.py"


def test_credential_spraying_plugin_remains_absent():
    assert not KERBRUTE_PLUGIN.exists()


def test_plugin_boundary_remains_fail_closed_and_non_executing_without_sandbox():
    sandbox_source = SANDBOX_RUNNER.read_text(encoding="utf-8")
    manager_source = PLUGIN_MANAGER.read_text(encoding="utf-8")

    assert "PLUGIN_SANDBOX_UNAVAILABLE" in sandbox_source
    assert "docker.from_env" in sandbox_source
    assert "manifest.json" in manager_source
