from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from phantomnet_core.command_signing import (
    COMMAND_SIGNATURE_ALGORITHM,
    sign_command,
    verify_command,
)


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR_PATH = ROOT / "phantomnet_agent/orchestrator.py"


def _command_envelope() -> dict[str, object]:
    return {
        "tenant_id": "tenant-001",
        "target_agent_id": "agent-007",
        "command_type": "collect_processes",
        "arguments": {"include_hashes": True},
        "task_id": "task-001",
        "issued_by": "analyst-001",
        "issued_at": "2026-08-23T00:00:00+00:00",
    }


def test_canonical_agent_command_signature_binds_the_complete_envelope():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    envelope = _command_envelope()

    signature = sign_command(envelope, private_key_pem)

    verify_command(envelope, signature, public_key_pem)
    assert COMMAND_SIGNATURE_ALGORITHM == "RSA-PSS-SHA256"

    tampered = {**envelope, "target_agent_id": "agent-008"}
    with pytest.raises(InvalidSignature):
        verify_command(tampered, signature, public_key_pem)


def test_malformed_or_missing_command_signature_is_rejected():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with pytest.raises(ValueError):
        verify_command(_command_envelope(), "", public_key_pem)
    with pytest.raises(Exception):
        verify_command(_command_envelope(), "not-base64!", public_key_pem)


def test_agent_orchestrator_preserves_and_verifies_the_complete_broker_envelope():
    source = ORCHESTRATOR_PATH.read_text(encoding="utf-8")

    assert '"command_envelope": command_data' in source
    assert "verify_command(command_envelope, signature, certificate_path.read_bytes())" in source
    assert "PHANTOMNET_ENFORCE_SIGNATURES" not in source
    assert "Skipping signature verification fallback" not in source
