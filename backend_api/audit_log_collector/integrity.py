"""Tamper-evident and optionally HMAC-signed audit records.

Hash chaining detects altered exports. HMAC signing authenticates each record when an
operator-provided signing key is available. This does not replace independent archival or
external anchoring for strong immutability guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
from typing import Any, Dict, Iterable


GENESIS_HASH = "0" * 64


def _canonical_json(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _key_bytes(signing_key: str | bytes) -> bytes:
    return signing_key.encode("utf-8") if isinstance(signing_key, str) else signing_key


def _signature(body: Dict[str, Any], record_hash: str, signing_key: str | bytes) -> str:
    message = f"{_canonical_json(body)}:{record_hash}".encode("utf-8")
    return hmac.new(_key_bytes(signing_key), message, sha256).hexdigest()


@dataclass(frozen=True)
class ChainedAuditRecord:
    record_id: str
    timestamp: str
    actor_id: str | None
    action: str
    payload: Dict[str, Any]
    previous_hash: str
    record_hash: str
    signature: str | None = None
    signature_key_id: str | None = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "action": self.action,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "record_hash": self.record_hash,
            "signature": self.signature,
            "signature_key_id": self.signature_key_id,
        }


def append_record(
    record_id: str,
    actor_id: str | None,
    action: str,
    payload: Dict[str, Any],
    previous_hash: str = GENESIS_HASH,
    signing_key: str | bytes | None = None,
    signature_key_id: str | None = None,
) -> ChainedAuditRecord:
    """Append one chained audit record and optionally authenticate it with HMAC-SHA-256."""
    timestamp = datetime.now(timezone.utc).isoformat()
    body = {
        "record_id": record_id,
        "timestamp": timestamp,
        "actor_id": actor_id,
        "action": action,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    record_hash = sha256(_canonical_json(body).encode("utf-8")).hexdigest()
    if signing_key is None:
        return ChainedAuditRecord(record_hash=record_hash, **body)
    if not signature_key_id:
        raise ValueError("signature_key_id is required when a signing_key is supplied")
    return ChainedAuditRecord(
        record_hash=record_hash,
        signature=_signature(body, record_hash, signing_key),
        signature_key_id=signature_key_id,
        **body,
    )


def verify_chain(
    records: Iterable[Dict[str, Any]],
    signing_key: str | bytes | None = None,
    require_signature: bool = False,
    expected_key_id: str | None = None,
) -> bool:
    """Verify record hashes, links, and optional HMAC signatures.

    ``require_signature`` rejects unsigned records. Supplying a signing key verifies each
    record signature in constant time and rejects any record with no signature.
    """
    previous_hash = GENESIS_HASH
    for record in records:
        try:
            body = {
                "record_id": record["record_id"],
                "timestamp": record["timestamp"],
                "actor_id": record.get("actor_id"),
                "action": record["action"],
                "payload": record["payload"],
                "previous_hash": record["previous_hash"],
            }
            record_hash = record["record_hash"]
        except (KeyError, TypeError):
            return False

        expected_hash = sha256(_canonical_json(body).encode("utf-8")).hexdigest()
        if record["previous_hash"] != previous_hash or not hmac.compare_digest(record_hash, expected_hash):
            return False

        signature = record.get("signature")
        key_id = record.get("signature_key_id")
        if require_signature and not signature:
            return False
        if expected_key_id is not None and key_id != expected_key_id:
            return False
        if signing_key is not None:
            if not signature or not key_id:
                return False
            expected_signature = _signature(body, record_hash, signing_key)
            if not hmac.compare_digest(signature, expected_signature):
                return False
        previous_hash = record_hash
    return True
