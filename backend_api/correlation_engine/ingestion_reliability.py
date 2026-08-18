"""Durable canonical-ingestion failure evidence and analyst-controlled replay.

Broker retry remains the first recovery mechanism. This module records a durable receipt only
when a caller decides a delivery has failed, and replay must be invoked explicitly with a tenant
scope and actor. It never dispatches response actions.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import AsyncSessionLocal, IngestionDeadLetterRow, engine
from phantomnet_core.contracts import BrokerDeliveryMetadata, IngestionDeadLetterRecord


SessionFactory = Callable[[], AsyncSession]
Processor = Callable[[Mapping[str, Any]], Awaitable[Any]]


class DeadLetterReplayError(ValueError):
    """Raised when a requested replay is outside the governed dead-letter lifecycle."""


class BrokerDeliveryRecordedError(RuntimeError):
    """Signals that canonical processing failed but durable dead-letter evidence was committed."""

    def __init__(self, receipt: IngestionDeadLetterRecord, cause: Exception) -> None:
        super().__init__(f"Canonical broker delivery was recorded as dead-letter evidence: {receipt.dead_letter_id}")
        self.receipt = receipt
        self.cause = cause


def _canonical_payload(message: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    """Bind a JSON broker message to a stable digest; fail rather than coercing arbitrary objects."""
    try:
        encoded = json.dumps(message, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload = json.loads(encoded.decode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Dead-letter evidence requires a JSON-serializable broker message.") from exc
    return payload, sha256(encoded).hexdigest()


def _tenant_id(message: Mapping[str, Any]) -> str | None:
    candidate = message.get("tenant_id")
    if not isinstance(candidate, str):
        return None
    try:
        return str(UUID(candidate))
    except ValueError:
        return None


def _event_id(message: Mapping[str, Any]) -> str | None:
    candidate = message.get("event_id")
    return candidate if isinstance(candidate, str) and candidate else None


def _failure_code(exc: Exception) -> str:
    if isinstance(exc, (ValidationError, ValueError)):
        return "CANONICAL_VALIDATION_FAILED"
    return "CANONICAL_PROCESSING_FAILED"


def _to_contract(row: IngestionDeadLetterRow) -> IngestionDeadLetterRecord:
    return IngestionDeadLetterRecord(
        dead_letter_id=row.dead_letter_id,
        tenant_id=str(row.tenant_id) if row.tenant_id else None,
        event_id=row.event_id,
        delivery=BrokerDeliveryMetadata(
            topic=row.topic,
            partition=row.partition,
            offset=row.offset,
            received_at=row.first_failed_at,
        ),
        message_hash=row.message_hash,
        payload=dict(row.payload),
        error_code=row.error_code,
        error_type=row.error_type,
        status=row.status,
        attempt_count=row.attempt_count,
        first_failed_at=row.first_failed_at,
        last_failed_at=row.last_failed_at,
        replayed_at=row.replayed_at,
        replayed_by=row.replayed_by,
    )


async def init_ingestion_dead_letter_store() -> None:
    """Provision durable failure evidence when migrations have not yet created the table."""
    async with engine.begin() as connection:
        await connection.run_sync(IngestionDeadLetterRow.__table__.create, checkfirst=True)


class IngestionDeadLetterRepository:
    """Persist each failed delivery once and update its retry evidence idempotently."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def record_failure(
        self,
        message: Mapping[str, Any],
        delivery: BrokerDeliveryMetadata,
        exc: Exception,
    ) -> tuple[IngestionDeadLetterRecord, bool]:
        payload, message_hash = _canonical_payload(message)
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(IngestionDeadLetterRow).where(
                    IngestionDeadLetterRow.topic == delivery.topic,
                    IngestionDeadLetterRow.partition == delivery.partition,
                    IngestionDeadLetterRow.offset == delivery.offset,
                )
            )
            if existing is not None:
                if existing.message_hash != message_hash:
                    raise ValueError("Broker delivery coordinates were reused with a different message hash.")
                if existing.status != "open":
                    return _to_contract(existing), False
                existing.attempt_count += 1
                existing.last_failed_at = now
                existing.error_code = _failure_code(exc)
                existing.error_type = type(exc).__name__
                await session.commit()
                return _to_contract(existing), False

            tenant_id = _tenant_id(payload)
            row = IngestionDeadLetterRow(
                dead_letter_id=str(uuid4()),
                tenant_id=UUID(tenant_id) if tenant_id else None,
                event_id=_event_id(payload),
                topic=delivery.topic,
                partition=delivery.partition,
                offset=delivery.offset,
                message_hash=message_hash,
                payload=payload,
                error_code=_failure_code(exc),
                error_type=type(exc).__name__,
                status="open",
                attempt_count=1,
                first_failed_at=now,
                last_failed_at=now,
                replayed_at=None,
                replayed_by=None,
            )
            session.add(row)
            await session.commit()
            return _to_contract(row), True

    async def list_for_tenant(self, tenant_id: str, limit: int = 100) -> list[IngestionDeadLetterRecord]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(IngestionDeadLetterRow)
                .where(IngestionDeadLetterRow.tenant_id == UUID(tenant_id))
                .order_by(IngestionDeadLetterRow.last_failed_at.desc())
                .limit(safe_limit)
            )
            return [_to_contract(row) for row in rows]

    async def replay(
        self,
        tenant_id: str,
        dead_letter_id: str,
        actor: str,
        processor: Processor,
    ) -> IngestionDeadLetterRecord:
        """Replay one open tenant-owned record exactly once; retain failure evidence on replay error."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(IngestionDeadLetterRow).where(
                    IngestionDeadLetterRow.tenant_id == UUID(tenant_id),
                    IngestionDeadLetterRow.dead_letter_id == dead_letter_id,
                )
            )
            if row is None:
                raise LookupError("Dead-letter record was not found for the authenticated tenant.")
            if row.status == "replayed":
                return _to_contract(row)
            if row.status != "open":
                raise DeadLetterReplayError("Only open dead-letter records may be replayed.")
            payload = dict(row.payload)
            expected_hash = row.message_hash
            delivery = BrokerDeliveryMetadata(
                topic=row.topic,
                partition=row.partition,
                offset=row.offset,
                received_at=row.first_failed_at,
            )

        replay_payload, replay_hash = _canonical_payload(payload)
        if replay_hash != expected_hash:
            raise DeadLetterReplayError("Dead-letter payload hash does not match its immutable delivery receipt.")
        try:
            await processor(replay_payload)
        except Exception as exc:
            await self.record_failure(replay_payload, delivery, exc)
            raise

        async with self._session_factory() as session:
            row = await session.scalar(
                select(IngestionDeadLetterRow).where(
                    IngestionDeadLetterRow.tenant_id == UUID(tenant_id),
                    IngestionDeadLetterRow.dead_letter_id == dead_letter_id,
                )
            )
            if row is None or row.status != "open":
                raise DeadLetterReplayError("Dead-letter replay state changed before completion.")
            row.status = "replayed"
            row.replayed_at = datetime.now(timezone.utc)
            row.replayed_by = actor
            await session.commit()
            return _to_contract(row)


class ReliableCanonicalIngestion:
    """Attach durable failure receipts to an existing canonical processor without changing success behavior."""

    def __init__(self, processor: Processor, dead_letters: IngestionDeadLetterRepository) -> None:
        self._processor = processor
        self._dead_letters = dead_letters

    async def process_delivery(self, message: Mapping[str, Any], delivery: BrokerDeliveryMetadata) -> Any:
        try:
            return await self._processor(message)
        except Exception as exc:
            receipt, _ = await self._dead_letters.record_failure(message, delivery, exc)
            raise BrokerDeliveryRecordedError(receipt, exc) from exc
