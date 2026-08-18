"""Secure multi-tenant Wazuh-compatible forwarder registration and live batch ingestion."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import secrets
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.shared.database import (
    AsyncSessionLocal,
    WazuhForwarderBatchRow,
    WazuhForwarderRow,
    engine,
)
from phantomnet_core.contracts import WazuhForwarderRecord, WazuhTelemetryBatch


SessionFactory = Callable[[], AsyncSession]


class ForwarderAuthenticationError(PermissionError):
    """Raised when a forwarder credential, status, or tenant binding is invalid."""


class ForwarderReplayError(ValueError):
    """Raised when an ordered batch is replayed, skipped, or otherwise out of sequence."""


def _forwarder_contract(row: WazuhForwarderRow) -> WazuhForwarderRecord:
    return WazuhForwarderRecord(
        forwarder_id=row.forwarder_id,
        tenant_id=str(row.tenant_id),
        name=row.name,
        status=row.status,
        created_by=row.created_by,
        created_at=row.created_at,
        last_seen_at=row.last_seen_at,
        last_sequence=row.last_sequence,
        automatic_enforcement=False,
    )


async def init_forwarder_store() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(WazuhForwarderRow.__table__.create, checkfirst=True)
        await connection.run_sync(WazuhForwarderBatchRow.__table__.create, checkfirst=True)


class WazuhForwarderService:
    """Manage credentialed telemetry-only forwarders and ordered Wazuh alert batches."""

    def __init__(
        self,
        session_factory: SessionFactory = AsyncSessionLocal,
        ingestion: EndpointTelemetryIngestion | None = None,
    ):
        self._session_factory = session_factory
        self._ingestion = ingestion or EndpointTelemetryIngestion()

    async def register(self, tenant_id: str, name: str, actor: str) -> tuple[WazuhForwarderRecord, str]:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(WazuhForwarderRow).where(
                    WazuhForwarderRow.tenant_id == UUID(tenant_id), WazuhForwarderRow.name == name
                )
            )
            if existing is not None:
                raise ValueError("A forwarder with this name already exists for the authenticated tenant.")
            row = WazuhForwarderRow(
                forwarder_id=secrets.token_urlsafe(18),
                tenant_id=UUID(tenant_id),
                name=name,
                token_digest=sha256(token.encode("utf-8")).hexdigest(),
                token_prefix=token[:8],
                status="active",
                created_by=actor,
                created_at=now,
                last_seen_at=None,
                last_sequence=0,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _forwarder_contract(row), token

    async def list_for_tenant(self, tenant_id: str) -> list[WazuhForwarderRecord]:
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(WazuhForwarderRow)
                .where(WazuhForwarderRow.tenant_id == UUID(tenant_id))
                .order_by(WazuhForwarderRow.created_at.desc())
            )
            return [_forwarder_contract(row) for row in rows]

    async def revoke(self, tenant_id: str, forwarder_id: str) -> WazuhForwarderRecord:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(WazuhForwarderRow).where(
                    WazuhForwarderRow.tenant_id == UUID(tenant_id), WazuhForwarderRow.forwarder_id == forwarder_id
                )
            )
            if row is None:
                raise LookupError("Forwarder was not found for the authenticated tenant.")
            row.status = "revoked"
            await session.commit()
            await session.refresh(row)
            return _forwarder_contract(row)

    async def _authenticated_forwarder(
        self, forwarder_id: str, token: str, session: AsyncSession
    ) -> WazuhForwarderRow:
        row = await session.scalar(
            select(WazuhForwarderRow).where(WazuhForwarderRow.forwarder_id == forwarder_id).with_for_update()
        )
        if row is None or row.status != "active":
            raise ForwarderAuthenticationError("Forwarder is unknown or inactive.")
        supplied_digest = sha256(token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(row.token_digest, supplied_digest):
            raise ForwarderAuthenticationError("Forwarder credential is invalid.")
        return row

    async def stream_batch(self, forwarder_id: str, token: str, batch: WazuhTelemetryBatch) -> dict[str, Any]:
        """Accept one live ordered Wazuh telemetry batch; no response action is possible here."""
        async with self._session_factory() as session:
            forwarder = await self._authenticated_forwarder(forwarder_id, token, session)
            expected_sequence = forwarder.last_sequence + 1
            if batch.sequence < expected_sequence:
                raise ForwarderReplayError("Telemetry batch sequence was already accepted or replayed.")
            if batch.sequence > expected_sequence:
                raise ForwarderReplayError(f"Telemetry batch sequence must be {expected_sequence}.")
            existing_batch = await session.scalar(
                select(WazuhForwarderBatchRow).where(
                    WazuhForwarderBatchRow.forwarder_id == forwarder_id,
                    WazuhForwarderBatchRow.batch_id == batch.batch_id,
                )
            )
            if existing_batch is not None:
                raise ForwarderReplayError("Telemetry batch ID was already accepted.")
            tenant_id = str(forwarder.tenant_id)

            asset_created = 0
            integrity_created = 0
            event_count = 0
            for alert in batch.alerts:
                result = await self._ingestion.ingest_wazuh_alert(tenant_id, alert)
                asset_created += int(bool(result["asset_created"]))
                integrity_created += int(bool(result.get("integrity_created", False)))
                event_count += len(result["events"])

            now = datetime.now(timezone.utc)
            session.add(
                WazuhForwarderBatchRow(
                    forwarder_id=forwarder.forwarder_id,
                    tenant_id=forwarder.tenant_id,
                    batch_id=batch.batch_id,
                    sequence=batch.sequence,
                    received_at=now,
                    alert_count=len(batch.alerts),
                )
            )
            forwarder.last_sequence = batch.sequence
            forwarder.last_seen_at = now
            await session.commit()
            await session.refresh(forwarder)
            return {
                "forwarder": _forwarder_contract(forwarder),
                "batch_id": batch.batch_id,
                "sequence": batch.sequence,
                "alert_count": len(batch.alerts),
                "asset_created": asset_created,
                "integrity_created": integrity_created,
                "canonical_event_count": event_count,
                "automatic_enforcement": False,
                "adapter_mode": "read_only_streaming",
            }

    async def request_containment(self, *_args: Any, **_kwargs: Any) -> None:
        raise PermissionError("Forwarder streaming is telemetry-only and cannot request containment.")
