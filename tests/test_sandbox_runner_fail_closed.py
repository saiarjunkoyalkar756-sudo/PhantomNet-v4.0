"""Regression coverage for fail-closed unavailable plugin sandbox execution."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RUNNER = ROOT / "backend_api/shared/sandbox_runner.py"
PLUGIN_MANAGER = ROOT / "backend_api/shared/plugin_manager.py"


def test_unavailable_sandbox_returns_explicit_error_without_fabricated_plugin_output():
    source = SANDBOX_RUNNER.read_text(encoding="utf-8")

    assert '"error": "PLUGIN_SANDBOX_UNAVAILABLE"' in source
    assert "no plugin result was produced" in source
    assert "MockDockerClient" not in source
    assert "Mocked Monitor" not in source
    assert "Simulated plugin output" not in source


def test_plugin_manager_keeps_plugin_execution_at_the_sandbox_boundary():
    source = PLUGIN_MANAGER.read_text(encoding="utf-8")

    assert "run_plugin_in_sandbox" in source
    assert 'return {"error": f"Failed to execute plugin function: {str(e)}"}' in source
