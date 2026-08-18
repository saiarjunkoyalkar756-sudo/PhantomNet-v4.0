"""Cross-region canonical telemetry replication with no response or command channel.

Only validated EventEnvelope telemetry is delivered. Replication state is receipt-based and
idempotent per tenant, regional target, and event. Adapters are injectable so deployments can use
a secured broker mirror while tests use an isolated transport.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from hashlib import sha256
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AsyncSessionLocal,
    TelemetryReplicationReceiptRow,
    TelemetryReplicationTargetRow,
    engine,
)
from phantomnet_core.contracts import EventEnvelope, TelemetryReplicationReceipt, TelemetryReplicationTarget


SessionFactory = Callable[[], AsyncSession]


class TelemetryReplicationTransport(Protocol):
    async def deliver(self, target: TelemetryReplicationTarget, event: EventEnvelope) -> None: ...


class DisabledTelemetryReplicationTransport:
    """Fail-closed default: no cross-region transport is attempted without explicit deployment wiring."""

    async def deliver(self, target: TelemetryReplicationTarget, event: EventEnvelope) -> None:
        raise RuntimeError("No telemetry replication transport is configured.")


class KafkaTelemetryReplicationTransport:
    """Lazy Kafka transport for canonical telemetry only; credentials remain in the deployment environment."""

    def __init__(
        self,
        bootstrap_servers: str,
        security_protocol: str = "SSL",
        ssl_cafile: str | None = None,
        ssl_certfile: str | None = None,
        ssl_keyfile: str | None = None,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._security_protocol = security_protocol
        self._ssl_cafile = ssl_cafile
        self._ssl_certfile = ssl_certfile
        self._ssl_keyfile = ssl_keyfile

    async def deliver(self, target: TelemetryReplicationTarget, event: EventEnvelope) -> None:
        payload = event.model_dump(mode="json")
        await asyncio.get_running_loop().run_in_executor(None, self._deliver_sync, target.stream_name, payload)

    def _deliver_sync(self, stream_name: str, payload: dict) -> None:
        from kafka import KafkaProducer

        options = {
            "bootstrap_servers": self._bootstrap_servers,
            "security_protocol": self._security_protocol,
            "value_serializer": lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            "request_timeout_ms": 5_000,
            "api_version_auto_timeout_ms": 5_000,
        }
        if self._ssl_cafile:
            options["ssl_cafile"] = self._ssl_cafile
        if self._ssl_certfile:
            options["ssl_certfile"] = self._ssl_certfile
        if self._ssl_keyfile:
            options["ssl_keyfile"] = self._ssl_keyfile
        producer = KafkaProducer(**options)
        try:
            producer.send(stream_name, payload).get(timeout=5)
            producer.flush(timeout=5)
        finally:
            producer.close(timeout=5)


def configured_telemetry_replication_transport() -> TelemetryReplicationTransport:
    """Return a transport only when operators explicitly enable a secured regional broker path."""
    enabled = os.getenv("PHANTOMNET_TELEMETRY_REPLICATION_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    bootstrap_servers = os.getenv("PHANTOMNET_REPLICATION_KAFKA_BOOTSTRAP_SERVERS", "").strip()
    if not enabled or not bootstrap_servers:
        return DisabledTelemetryReplicationTransport()
    return KafkaTelemetryReplicationTransport(
        bootstrap_servers=bootstrap_servers,
        security_protocol=os.getenv("PHANTOMNET_REPLICATION_KAFKA_SECURITY_PROTOCOL", "SSL").strip().upper(),
        ssl_cafile=os.getenv("PHANTOMNET_REPLICATION_KAFKA_SSL_CAFILE") or None,
        ssl_certfile=os.getenv("PHANTOMNET_REPLICATION_KAFKA_SSL_CERTFILE") or None,
        ssl_keyfile=os.getenv("PHANTOMNET_REPLICATION_KAFKA_SSL_KEYFILE") or None,
    )


def _target_contract(row: TelemetryReplicationTargetRow) -> TelemetryReplicationTarget:
    return TelemetryReplicationTarget(
        target_id=row.target_id,
        tenant_id=str(row.tenant_id),
        target_region=row.target_region,
        stream_name=row.stream_name,
        enabled=row.enabled,
        telemetry_only=True,
    )


def _receipt_contract(row: TelemetryReplicationReceiptRow) -> TelemetryReplicationReceipt:
    return TelemetryReplicationReceipt(
        receipt_id=row.receipt_id,
        tenant_id=str(row.tenant_id),
        target_id=row.target_id,
        event_id=row.event_id,
        source_region=row.source_region,
        target_region=row.target_region,
        payload_hash=row.payload_hash,
        status=row.status,
        attempt_count=row.attempt_count,
        created_at=row.created_at,
        delivered_at=row.delivered_at,
        error_code=row.error_code,
        automatic_enforcement=False,
    )


def _event_hash(event: EventEnvelope) -> str:
    encoded = json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


async def init_telemetry_replication_store() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(TelemetryReplicationTargetRow.__table__.create, checkfirst=True)
        await connection.run_sync(TelemetryReplicationReceiptRow.__table__.create, checkfirst=True)


class TelemetryReplicationRepository:
    """Tenant-safe target and receipt persistence; no endpoint credentials are stored here."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def upsert_target(self, target: TelemetryReplicationTarget) -> TelemetryReplicationTarget:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(TelemetryReplicationTargetRow).where(
                    TelemetryReplicationTargetRow.tenant_id == UUID(target.tenant_id),
                    TelemetryReplicationTargetRow.target_region == target.target_region,
                    TelemetryReplicationTargetRow.stream_name == target.stream_name,
                )
            )
            now = datetime.now(timezone.utc)
            if row is None:
                row = TelemetryReplicationTargetRow(
                    target_id=target.target_id,
                    tenant_id=UUID(target.tenant_id),
                    target_region=target.target_region,
                    stream_name=target.stream_name,
                    enabled=target.enabled,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.enabled = target.enabled
                row.updated_at = now
            await session.commit()
            return _target_contract(row)

    async def list_targets(self, tenant_id: str, enabled_only: bool = False) -> list[TelemetryReplicationTarget]:
        async with self._session_factory() as session:
            statement = select(TelemetryReplicationTargetRow).where(TelemetryReplicationTargetRow.tenant_id == UUID(tenant_id))
            if enabled_only:
                statement = statement.where(TelemetryReplicationTargetRow.enabled.is_(True))
            rows = await session.scalars(statement.order_by(TelemetryReplicationTargetRow.target_region, TelemetryReplicationTargetRow.stream_name))
            return [_target_contract(row) for row in rows]

    async def reserve_receipt(
        self,
        event: EventEnvelope,
        target: TelemetryReplicationTarget,
        source_region: str,
    ) -> tuple[TelemetryReplicationReceipt, bool]:
        payload_hash = _event_hash(event)
        async with self._session_factory() as session:
            row = await session.scalar(
                select(TelemetryReplicationReceiptRow).where(
                    TelemetryReplicationReceiptRow.tenant_id == UUID(event.tenant_id),
                    TelemetryReplicationReceiptRow.target_id == target.target_id,
                    TelemetryReplicationReceiptRow.event_id == event.event_id,
                )
            )
            if row is not None:
                if row.payload_hash != payload_hash:
                    raise ValueError("Replication receipt event identity was reused with a different payload hash.")
                if row.status == "delivered":
                    return _receipt_contract(row), False
                row.attempt_count += 1
                row.status = "pending"
                row.error_code = None
                await session.commit()
                return _receipt_contract(row), True
            now = datetime.now(timezone.utc)
            row = TelemetryReplicationReceiptRow(
                receipt_id=str(uuid4()),
                tenant_id=UUID(event.tenant_id),
                target_id=target.target_id,
                event_id=event.event_id,
                source_region=source_region,
                target_region=target.target_region,
                payload_hash=payload_hash,
                status="pending",
                attempt_count=1,
                created_at=now,
                delivered_at=None,
                error_code=None,
            )
            session.add(row)
            await session.commit()
            return _receipt_contract(row), True

    async def mark_delivered(self, tenant_id: str, receipt_id: str) -> TelemetryReplicationReceipt:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(TelemetryReplicationReceiptRow).where(
                    TelemetryReplicationReceiptRow.tenant_id == UUID(tenant_id),
                    TelemetryReplicationReceiptRow.receipt_id == receipt_id,
                )
            )
            if row is None:
                raise LookupError("Replication receipt was not found for the authenticated tenant.")
            row.status = "delivered"
            row.delivered_at = datetime.now(timezone.utc)
            row.error_code = None
            await session.commit()
            return _receipt_contract(row)

    async def mark_failed(self, tenant_id: str, receipt_id: str, error_code: str) -> TelemetryReplicationReceipt:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(TelemetryReplicationReceiptRow).where(
                    TelemetryReplicationReceiptRow.tenant_id == UUID(tenant_id),
                    TelemetryReplicationReceiptRow.receipt_id == receipt_id,
                )
            )
            if row is None:
                raise LookupError("Replication receipt was not found for the authenticated tenant.")
            row.status = "failed"
            row.error_code = error_code[:120]
            await session.commit()
            return _receipt_contract(row)

    async def list_receipts(self, tenant_id: str, limit: int = 100) -> list[TelemetryReplicationReceipt]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(TelemetryReplicationReceiptRow)
                .where(TelemetryReplicationReceiptRow.tenant_id == UUID(tenant_id))
                .order_by(TelemetryReplicationReceiptRow.created_at.desc())
                .limit(safe_limit)
            )
            return [_receipt_contract(row) for row in rows]


class TelemetryReplicationService:
    """Delivers telemetry to explicit regional targets and records every result without blocking canonical detection."""

    def __init__(
        self,
        repository: TelemetryReplicationRepository,
        transport: TelemetryReplicationTransport | None = None,
        source_region: str = "local",
    ) -> None:
        self._repository = repository
        self._transport = transport or DisabledTelemetryReplicationTransport()
        self._source_region = source_region

    async def replicate_event(self, event: EventEnvelope) -> Sequence[TelemetryReplicationReceipt]:
        receipts: list[TelemetryReplicationReceipt] = []
        for target in await self._repository.list_targets(event.tenant_id, enabled_only=True):
            if target.target_region == self._source_region:
                continue
            receipt, should_deliver = await self._repository.reserve_receipt(event, target, self._source_region)
            if not should_deliver:
                receipts.append(receipt)
                continue
            try:
                await self._transport.deliver(target, event)
            except Exception as exc:
                receipts.append(await self._repository.mark_failed(event.tenant_id, receipt.receipt_id, type(exc).__name__))
            else:
                receipts.append(await self._repository.mark_delivered(event.tenant_id, receipt.receipt_id))
        return receipts
