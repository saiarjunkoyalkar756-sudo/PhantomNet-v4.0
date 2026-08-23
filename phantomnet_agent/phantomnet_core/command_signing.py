"""Canonical, fail-closed signing helpers for governed agent command envelopes."""

from __future__ import annotations

import base64
import json
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


COMMAND_SIGNING_DOMAIN = "phantomnet.agent-command.v1"
COMMAND_SIGNATURE_ALGORITHM = "RSA-PSS-SHA256"
_REQUIRED_COMMAND_FIELDS = (
    "tenant_id",
    "target_agent_id",
    "command_type",
    "arguments",
    "task_id",
    "issued_by",
    "issued_at",
)


def canonical_command_bytes(command: Mapping[str, Any]) -> bytes:
    """Serialize exactly the complete governed command identity bound by a signature."""
    missing = [field for field in _REQUIRED_COMMAND_FIELDS if field not in command]
    if missing:
        raise ValueError(f"Command envelope missing required fields: {', '.join(missing)}")
    if not isinstance(command["arguments"], Mapping):
        raise ValueError("Command envelope arguments must be an object.")

    envelope = {field: command[field] for field in _REQUIRED_COMMAND_FIELDS}
    envelope["domain"] = COMMAND_SIGNING_DOMAIN
    return json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sign_command(command: Mapping[str, Any], private_key_pem: str | bytes) -> str:
    """Return a base64 RSA-PSS/SHA-256 detached signature for a canonical command."""
    key_material = private_key_pem.encode("utf-8") if isinstance(private_key_pem, str) else private_key_pem
    private_key = serialization.load_pem_private_key(key_material, password=None)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("Command signing key must be an RSA private key.")
    signature = private_key.sign(
        canonical_command_bytes(command),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("ascii")


def verify_command(command: Mapping[str, Any], signature: str, certificate_or_public_key_pem: str | bytes) -> None:
    """Raise when a detached command signature cannot be verified by the trusted key."""
    if not signature:
        raise ValueError("Command signature is required.")
    trusted_material = (
        certificate_or_public_key_pem.encode("utf-8")
        if isinstance(certificate_or_public_key_pem, str)
        else certificate_or_public_key_pem
    )
    try:
        public_key = serialization.load_pem_public_key(trusted_material)
    except ValueError:
        from cryptography import x509

        public_key = x509.load_pem_x509_certificate(trusted_material).public_key()
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("Trusted command signing key must be an RSA public key.")
    try:
        decoded_signature = base64.b64decode(signature, validate=True)
    except ValueError as exc:
        raise ValueError("Command signature is not valid base64.") from exc
    try:
        public_key.verify(
            decoded_signature,
            canonical_command_bytes(command),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
            hashes.SHA256(),
        )
    except InvalidSignature:
        raise
