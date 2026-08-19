#!/usr/bin/env python3
"""Wazuh custom Active Response verifier for PhantomNet's governed bridge.

This script is deliberately not a firewall implementation. It verifies the exact signed command
from PhantomNet and invokes one operator-reviewed local executor only when all controls pass.
Without a configured executor that independently proves state, it exits nonzero and emits no
success receipt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4


MAX_INPUT_BYTES = 1_048_576
EXPECTED_ARGUMENT_COUNT = 9
ENVIRONMENT_FILE = Path("/var/ossec/etc/phantomnet-response.env")
ALLOWED_ENVIRONMENT_KEYS = {
    "PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY",
    "PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY_ID",
    "PHANTOMNET_WAZUH_RESPONSE_RECEIPT_URL",
    "PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY",
    "PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY_ID",
    "PHANTOMNET_WAZUH_RESPONSE_ALLOWED_MANAGEMENT_CIDRS",
    "PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED",
    "PHANTOMNET_WAZUH_RESPONSE_EXECUTOR",
}


def _load_environment() -> None:
    try:
        lines = ENVIRONMENT_FILE.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Cannot read {ENVIRONMENT_FILE}.") from exc
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = stripped.partition("=")
        if not separator or key not in ALLOWED_ENVIRONMENT_KEYS:
            raise ValueError("Response environment file contains an invalid setting.")
        os.environ.setdefault(key, value)


def _fail(detail: str) -> int:
    print(f"PhantomNet Wazuh response refused: {detail}", file=sys.stderr)
    return 1


def _environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required.")
    return value


def _active_response_message() -> dict:
    raw = sys.stdin.buffer.readline(MAX_INPUT_BYTES + 1)
    if not raw or len(raw) > MAX_INPUT_BYTES:
        raise ValueError("Wazuh Active Response input is missing or too large.")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Wazuh Active Response input is not valid JSON.") from exc
    if not isinstance(value, dict) or value.get("command") != "add":
        raise ValueError("Wazuh Active Response command must be a stateless add action.")
    return value


def _extra_arguments(message: dict) -> list[str]:
    parameters = message.get("parameters")
    candidates = parameters.get("extra_args") if isinstance(parameters, dict) else None
    if not isinstance(candidates, list) or len(candidates) != EXPECTED_ARGUMENT_COUNT or not all(isinstance(item, str) and item for item in candidates):
        raise ValueError("Wazuh Active Response command did not contain the required bounded argument envelope.")
    return candidates


def _action_from_invocation() -> tuple[str, str]:
    if len(sys.argv) < 3 or sys.argv[1] != "--mode":
        raise ValueError("Response verifier must be invoked by an approved fixed-mode wrapper.")
    if sys.argv[2] == "isolate":
        return "isolate_endpoint", "isolated"
    if sys.argv[2] == "release":
        return "release_endpoint", "released"
    raise ValueError("Unexpected Wazuh Active Response mode.")


def _command_fingerprint(*, tenant_id: str, request_id: str, approval_id: str, agent_id: str, action: str, profile: str, management_cidr: str) -> str:
    bound = {
        "action": action,
        "approval_id": approval_id,
        "asset_id": agent_id,
        "management_cidr": management_cidr,
        "request_id": request_id,
        "response_profile": profile,
        "tenant_id": tenant_id,
        "wazuh_agent_id": agent_id,
    }
    return sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _validate_envelope(message: dict, action: str) -> dict[str, str]:
    tenant_id, request_id, approval_id, agent_id, profile, management_cidr, fingerprint, key_id, signature = _extra_arguments(message)
    alert_agent_id = message.get("parameters", {}).get("alert", {}).get("agent", {}).get("id")
    if str(alert_agent_id) != agent_id:
        raise ValueError("Wazuh alert agent ID does not match the approved command target.")
    if management_cidr not in {value.strip() for value in os.getenv("PHANTOMNET_WAZUH_RESPONSE_ALLOWED_MANAGEMENT_CIDRS", "").split(",") if value.strip()}:
        raise ValueError("Management CIDR is not allowlisted on this endpoint.")
    ipaddress.ip_network(management_cidr, strict=False)
    expected_fingerprint = _command_fingerprint(
        tenant_id=tenant_id,
        request_id=request_id,
        approval_id=approval_id,
        agent_id=agent_id,
        action=action,
        profile=profile,
        management_cidr=management_cidr,
    )
    if not hmac.compare_digest(expected_fingerprint, fingerprint):
        raise ValueError("Command fingerprint does not bind the approved action and target fields.")
    expected_key_id = _environment("PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY_ID")
    if key_id != expected_key_id:
        raise ValueError("Command signature key ID is not trusted by this endpoint.")
    expected_signature = hmac.new(_environment("PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY").encode("utf-8"), fingerprint.encode("ascii"), sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        raise ValueError("Command signature is invalid.")
    return {
        "tenant_id": tenant_id,
        "request_id": request_id,
        "approval_id": approval_id,
        "agent_id": agent_id,
        "profile": profile,
        "management_cidr": management_cidr,
        "fingerprint": fingerprint,
    }


def _run_verified_executor(action: str, envelope: dict[str, str]) -> None:
    if os.getenv("PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED", "false").lower() != "true":
        raise ValueError("Local response enforcement is disabled by default.")
    executor = Path(_environment("PHANTOMNET_WAZUH_RESPONSE_EXECUTOR"))
    if not executor.is_file() or not os.access(executor, os.X_OK):
        raise ValueError("Configured local response executor is unavailable or not executable.")
    response = subprocess.run(
        [
            str(executor),
            "--action",
            action,
            "--profile",
            envelope["profile"],
            "--management-cidr",
            envelope["management_cidr"],
            "--request-id",
            envelope["request_id"],
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if response.returncode != 0:
        raise ValueError("Local response executor returned a failure status.")
    try:
        evidence = json.loads(response.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Local response executor did not return JSON verification evidence.") from exc
    expected_state = "isolated" if action == "isolate_endpoint" else "released"
    if not isinstance(evidence, dict) or evidence.get("verified") is not True or evidence.get("network_state") != expected_state:
        raise ValueError("Local response executor did not independently verify the expected endpoint state.")


def _post_receipt(action: str, network_state: str, envelope: dict[str, str]) -> None:
    receipt_url = _environment("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_URL")
    parsed = urlparse(receipt_url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("Response receipt callback must use HTTPS.")
    observed_at = datetime.now(timezone.utc).isoformat()
    unsigned = {
        "receipt_id": str(uuid4()),
        "tenant_id": envelope["tenant_id"],
        "request_id": envelope["request_id"],
        "approval_id": envelope["approval_id"],
        "asset_id": envelope["agent_id"],
        "wazuh_agent_id": envelope["agent_id"],
        "action": action,
        "network_state": network_state,
        "command_fingerprint": envelope["fingerprint"],
        "nonce": str(uuid4()),
        "observed_at": observed_at,
        "signature_key_id": _environment("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY_ID"),
    }
    canonical = json.dumps({key: str(value) for key, value in unsigned.items()}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt = {**unsigned, "signature": hmac.new(_environment("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY").encode("utf-8"), canonical, sha256).hexdigest()}
    request = Request(
        receipt_url,
        data=json.dumps(receipt, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - endpoint is explicitly HTTPS-validated above.
            if response.status != 202:
                raise ValueError(f"Receipt callback returned HTTP {response.status}.")
    except HTTPError as exc:
        raise ValueError(f"Receipt callback returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError) as exc:
        raise ValueError("Receipt callback is unavailable; containment cannot be verified.") from exc


def main() -> int:
    try:
        _load_environment()
        action, expected_state = _action_from_invocation()
        envelope = _validate_envelope(_active_response_message(), action)
        _run_verified_executor(action, envelope)
        _post_receipt(action, expected_state, envelope)
        return 0
    except (ValueError, subprocess.TimeoutExpired) as exc:
        return _fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
