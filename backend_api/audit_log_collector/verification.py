"""Verification of persisted tenant-scoped containment audit chains.

Verification is intentionally read-only. It reports whether stored records remain internally
consistent with their SHA-256 chain and optional HMAC key identity; it never repairs, rewrites,
or suppresses invalid evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.audit_log_collector.integrity import verify_chain
from backend_api.shared.database import AsyncSessionLocal, ContainmentAuditRecordRow


SessionFactory = Callable[[], AsyncSession]


@dataclass(frozen=True)
class AuditChainVerification:
    tenant_id: str
    record_count: int
    valid: bool
    require_signature: bool
    expected_key_id: str | None


def _timestamp_text(value: Any) -> str:
    """Preserve canonical UTC ISO formatting across PostgreSQL and SQLite retrieval."""
    if isinstance(value, str):
        return value
    if getattr(value, "tzinfo", None) is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


def _record_payload(row: ContainmentAuditRecordRow) -> dict[str, Any]:
    return {
        "record_id": row.record_id,
        "timestamp": _timestamp_text(row.timestamp),
        "actor_id": row.actor_id,
        "action": row.action,
        "payload": dict(row.payload),
        "previous_hash": row.previous_hash,
        "record_hash": row.record_hash,
        "signature": row.signature,
        "signature_key_id": row.signature_key_id,
    }


class ContainmentAuditVerifier:
    """Read-only verifier for a single tenant's ordered containment audit chain."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def verify_tenant(
        self,
        tenant_id: str,
        signing_key: str | bytes | None = None,
        require_signature: bool = True,
        expected_key_id: str | None = None,
    ) -> AuditChainVerification:
        async with self._session_factory() as session:
            rows = list(
                await session.scalars(
                    select(ContainmentAuditRecordRow)
                    .where(ContainmentAuditRecordRow.tenant_id == UUID(tenant_id))
                    .order_by(ContainmentAuditRecordRow.id)
                )
            )
        valid = verify_chain(
            [_record_payload(row) for row in rows],
            signing_key=signing_key,
            require_signature=require_signature,
            expected_key_id=expected_key_id,
        )
        return AuditChainVerification(
            tenant_id=str(UUID(tenant_id)),
            record_count=len(rows),
            valid=valid,
            require_signature=require_signature,
            expected_key_id=expected_key_id,
        )
