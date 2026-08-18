from __future__ import annotations

from pathlib import Path
import subprocess

from backend_api.soar_engine.local_enforcement import (
    CONFIRM_VALUE,
    LocalEnforcementAdapter,
)


class StatefulIptablesRunner:
    """Test double that models only adapter-owned iptables commands."""

    def __init__(self) -> None:
        self.rules: set[str] = set()
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        self.commands.append(list(command))
        operation = command[2]
        target = command[5]
        if operation == "-C":
            return subprocess.CompletedProcess(command, 0 if target in self.rules else 1, "", "")
        if operation == "-I":
            self.rules.add(target)
            return subprocess.CompletedProcess(command, 0, "", "")
        if operation == "-D":
            self.rules.discard(target)
            return subprocess.CompletedProcess(command, 0, "", "")
        raise AssertionError(f"Unexpected operation: {operation}")


def test_dry_run_is_truthful_and_non_enforcing(tmp_path: Path):
    runner = StatefulIptablesRunner()
    adapter = LocalEnforcementAdapter(
        mode="dry-run",
        command_runner=runner,
        command_available=lambda _: "/usr/sbin/iptables",
        audit_path=tmp_path / "audit.log",
    )

    result = adapter.block_ip("198.51.100.42")

    assert result["status"] == "success"
    assert result["enforced"] is False
    assert result["verified"] is False
    assert runner.commands == []
    assert "Dry-run" in str(result["detail"])


def test_rejects_non_documentation_addresses_without_command_execution(tmp_path: Path):
    runner = StatefulIptablesRunner()
    adapter = LocalEnforcementAdapter(
        mode="enabled",
        confirmation=CONFIRM_VALUE,
        command_runner=runner,
        command_available=lambda _: "/usr/sbin/iptables",
        audit_path=tmp_path / "audit.log",
    )

    result = adapter.block_ip("8.8.8.8")

    assert result["status"] == "failure"
    assert result["enforced"] is False
    assert runner.commands == []
    assert "Only RFC 5737 documentation addresses" in str(result["detail"])


def test_enabled_mode_applies_verifies_and_rolls_back_allowlisted_rule(tmp_path: Path):
    runner = StatefulIptablesRunner()
    adapter = LocalEnforcementAdapter(
        mode="enabled",
        confirmation=CONFIRM_VALUE,
        command_runner=runner,
        command_available=lambda _: "/usr/sbin/iptables",
        audit_path=tmp_path / "audit.log",
    )

    applied = adapter.block_ip("203.0.113.7")
    rolled_back = adapter.rollback_block_ip("203.0.113.7")

    assert applied["status"] == "success"
    assert applied["enforced"] is True
    assert applied["verified"] is True
    assert rolled_back["status"] == "success"
    assert rolled_back["rolled_back"] is True
    assert rolled_back["verified"] is True
    assert runner.rules == set()
    assert "event=block_ip" in (tmp_path / "audit.log").read_text(encoding="utf-8")
    assert "event=rollback_block_ip" in (tmp_path / "audit.log").read_text(encoding="utf-8")


def test_host_isolation_is_honest_when_no_endpoint_provider_exists(tmp_path: Path):
    adapter = LocalEnforcementAdapter(mode="dry-run", audit_path=tmp_path / "audit.log")

    result = adapter.isolate_host("validation-host")

    assert result["status"] == "failure"
    assert result["enforced"] is False
    assert result["verified"] is False
