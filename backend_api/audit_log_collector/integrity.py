"""Tamper-evident audit record chaining for verifiable exports.

This supports integrity verification but does not claim immutable external storage.  For
stronger guarantees, periodically anchor exported chain heads into an independently
controlled ledger or object-lock storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Dict, Iterable


GENESIS_HASH = "0" * 64


def _canonical_json(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class ChainedAuditRecord:
    record_id: str
    timestamp: str
    actor_id: str | None
    action: str
    payload: Dict[str, Any]
    previous_hash: str
    record_hash: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "action": self.action,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "record_hash": self.record_hash,
        }


def append_record(record_id: str, actor_id: str | None, action: str, payload: Dict[str, Any], previous_hash: str = GENESIS_HASH) -> ChainedAuditRecord:
    timestamp = datetime.now(timezone.utc).isoformat()
    body = {
        "record_id": record_id,
        "timestamp": timestamp,
        "actor_id": actor_id,
        "action": action,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    return ChainedAuditRecord(record_hash=sha256(_canonical_json(body).encode("utf-8")).hexdigest(), **body)


def verify_chain(records: Iterable[Dict[str, Any]]) -> bool:
    previous_hash = GENESIS_HASH
    for record in records:
        body = {
            "record_id": record["record_id"],
            "timestamp": record["timestamp"],
            "actor_id": record.get("actor_id"),
            "action": record["action"],
            "payload": record["payload"],
            "previous_hash": record["previous_hash"],
        }
        expected_hash = sha256(_canonical_json(body).encode("utf-8")).hexdigest()
        if record["previous_hash"] != previous_hash or record["record_hash"] != expected_hash:
            return False
        previous_hash = record["record_hash"]
    return True
