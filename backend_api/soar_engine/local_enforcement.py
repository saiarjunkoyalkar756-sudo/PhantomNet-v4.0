"""Constrained local firewall enforcement for PhantomNet SOAR.

This adapter is intentionally narrow.  It can enforce a local outbound reject rule only
for RFC 5737 documentation networks, and only when explicit environment safeguards are
set.  Production firewall/EDR integrations must be implemented as separate providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Sequence


logger = logging.getLogger(__name__)

DOCUMENTATION_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")
)
MODE_ENV = "PHANTOMNET_LOCAL_ENFORCEMENT_MODE"
CONFIRM_ENV = "PHANTOMNET_LOCAL_ENFORCEMENT_CONFIRM"
CONFIRM_VALUE = "I_UNDERSTAND_LOCAL_FIREWALL_CHANGES"
RULE_COMMENT = "phantomnet-local"


@dataclass(frozen=True)
class EnforcementResult:
    status: str
    detail: str
    target: str
    enforced: bool
    verified: bool
    rolled_back: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "detail": self.detail,
            "target": self.target,
            "enforced": self.enforced,
            "verified": self.verified,
            "rolled_back": self.rolled_back,
        }


class LocalEnforcementAdapter:
    """Apply and verify a narrowly-scoped local iptables reject rule.

    The adapter defaults to dry-run.  Real rule changes require an explicit mode and
    confirmation token.  Targets outside documentation networks are rejected before
    any command is executed.
    """

    def __init__(
        self,
        mode: str | None = None,
        confirmation: str | None = None,
        command_runner: Callable[[Sequence[str]], subprocess.CompletedProcess[str]] | None = None,
        command_available: Callable[[str], str | None] | None = None,
        audit_path: Path | None = None,
    ) -> None:
        self.mode = (mode or os.getenv(MODE_ENV, "dry-run")).strip().lower()
        self.confirmation = confirmation if confirmation is not None else os.getenv(CONFIRM_ENV, "")
        self.command_runner = command_runner or self._run_command
        self.command_available = command_available or shutil.which
        self.audit_path = audit_path or Path(__file__).resolve().parents[2] / "logs" / "local_enforcement_audit.log"

    @staticmethod
    def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(list(command), text=True, capture_output=True, check=False, timeout=10)

    @staticmethod
    def _is_allowed_target(ip_address: str) -> bool:
        try:
            address = ipaddress.ip_address(ip_address)
        except ValueError:
            return False
        return any(address in network for network in DOCUMENTATION_NETWORKS)

    @staticmethod
    def _rule_command(operation: str, ip_address: str) -> list[str]:
        return [
            "iptables", "-w", operation, "OUTPUT", "-d", ip_address,
            "-m", "comment", "--comment", RULE_COMMENT, "-j", "REJECT",
        ]

    def _audit(self, event: str, result: EnforcementResult) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        record = (
            f"{datetime.now(timezone.utc).isoformat()} event={event} mode={self.mode} "
            f"target={result.target} status={result.status} enforced={result.enforced} "
            f"verified={result.verified} rolled_back={result.rolled_back} detail={result.detail}\n"
        )
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(record)

    def _failure(self, target: str, detail: str) -> dict[str, object]:
        result = EnforcementResult("failure", detail, target, False, False)
        self._audit("block_ip", result)
        return result.as_dict()

    def _is_enabled(self) -> bool:
        return self.mode == "enabled" and self.confirmation == CONFIRM_VALUE

    def _verify_rule(self, ip_address: str) -> bool:
        completed = self.command_runner(self._rule_command("-C", ip_address))
        return completed.returncode == 0

    def block_ip(self, ip_address: str) -> dict[str, object]:
        """Block local outbound traffic to an allowlisted documentation address."""
        if not self._is_allowed_target(ip_address):
            return self._failure(
                ip_address,
                "Local enforcement rejected the target. Only RFC 5737 documentation addresses are permitted.",
            )
        if self.mode not in {"dry-run", "enabled"}:
            return self._failure(ip_address, f"Unsupported local enforcement mode: {self.mode}.")
        if self.mode == "dry-run":
            result = EnforcementResult(
                "success",
                f"Dry-run: would add a local outbound reject rule for {ip_address}.",
                ip_address,
                False,
                False,
            )
            self._audit("block_ip", result)
            return result.as_dict()
        if self.confirmation != CONFIRM_VALUE:
            return self._failure(ip_address, "Explicit local firewall confirmation token is required.")
        if not self.command_available("iptables"):
            return self._failure(ip_address, "iptables is unavailable on this host.")
        if self._verify_rule(ip_address):
            result = EnforcementResult(
                "success",
                f"Existing local outbound reject rule verified for {ip_address}.",
                ip_address,
                True,
                True,
            )
            self._audit("block_ip", result)
            return result.as_dict()

        completed = self.command_runner(self._rule_command("-I", ip_address))
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "iptables rejected the rule."
            return self._failure(ip_address, f"Unable to add local reject rule: {detail}")

        verified = self._verify_rule(ip_address)
        result = EnforcementResult(
            "success" if verified else "failure",
            (
                f"Local outbound reject rule applied and verified for {ip_address}."
                if verified
                else f"Rule insertion returned success but verification failed for {ip_address}."
            ),
            ip_address,
            verified,
            verified,
        )
        self._audit("block_ip", result)
        return result.as_dict()

    def rollback_block_ip(self, ip_address: str) -> dict[str, object]:
        """Remove the adapter-owned rule for an allowlisted documentation address."""
        if not self._is_allowed_target(ip_address):
            return self._failure(ip_address, "Rollback rejected the target outside the local-test allowlist.")
        if not self._is_enabled():
            return self._failure(ip_address, "Rollback requires enabled mode and the explicit confirmation token.")
        if not self.command_available("iptables"):
            return self._failure(ip_address, "iptables is unavailable on this host.")
        if not self._verify_rule(ip_address):
            result = EnforcementResult(
                "success",
                f"No adapter-owned rule exists for {ip_address}; nothing to roll back.",
                ip_address,
                False,
                True,
                True,
            )
            self._audit("rollback_block_ip", result)
            return result.as_dict()

        completed = self.command_runner(self._rule_command("-D", ip_address))
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "iptables rejected the rollback."
            return self._failure(ip_address, f"Unable to remove local reject rule: {detail}")
        verified_removed = not self._verify_rule(ip_address)
        result = EnforcementResult(
            "success" if verified_removed else "failure",
            (
                f"Local outbound reject rule removed and rollback verified for {ip_address}."
                if verified_removed
                else f"Rollback command returned success but the rule remains for {ip_address}."
            ),
            ip_address,
            False,
            verified_removed,
            verified_removed,
        )
        self._audit("rollback_block_ip", result)
        return result.as_dict()

    def isolate_host(self, hostname: str) -> dict[str, object]:
        """Refuse host isolation until a supported endpoint provider is configured."""
        result = EnforcementResult(
            "failure",
            f"Host isolation for {hostname} requires a configured endpoint-management provider; no local host isolation was performed.",
            hostname,
            False,
            False,
        )
        self._audit("isolate_host", result)
        return result.as_dict()


_default_adapter: LocalEnforcementAdapter | None = None


def get_local_enforcement_adapter() -> LocalEnforcementAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = LocalEnforcementAdapter()
    return _default_adapter
