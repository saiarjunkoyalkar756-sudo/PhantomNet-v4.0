"""Durable tenant-scoped endpoint asset and integrity evidence repositories."""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AsyncSessionLocal,
    EndpointAssetRow,
    HostIntegrityObservationRow,
    engine,
)
from phantomnet_core.contracts import HostAssetRecord, IntegrityObservation


SessionFactory = Callable[[], AsyncSession]


def _asset_contract(row: EndpointAssetRow) -> HostAssetRecord:
    return HostAssetRecord(
        asset_id=row.asset_id,
        tenant_id=str(row.tenant_id),
        agent_id=row.agent_id,
        hostname=row.hostname,
        platform=row.platform,
        os_version=row.os_version,
        ip_addresses=list(row.ip_addresses),
        software=list(row.software),
        tags=list(row.tags),
        source=row.source,
        last_seen=row.last_seen,
        evidence=dict(row.evidence),
    )


def _integrity_contract(row: HostIntegrityObservationRow) -> IntegrityObservation:
    return IntegrityObservation(
        observation_id=row.observation_id,
        tenant_id=str(row.tenant_id),
        asset_id=row.asset_id,
        agent_id=row.agent_id,
        source_event_id=row.source_event_id,
        source=row.source,
        check_type=row.check_type,
        status=row.status,
        severity=row.severity,
        observed_at=row.observed_at,
        path=row.path,
        observed_hash=row.observed_hash,
        expected_hash=row.expected_hash,
        evidence=dict(row.evidence),
        automatic_enforcement=bool(row.automatic_enforcement),
    )


async def init_endpoint_inventory_store() -> None:
    """Provision endpoint persistence in environments where migrations have not run yet."""
    async with engine.begin() as connection:
        await connection.run_sync(EndpointAssetRow.__table__.create, checkfirst=True)
        await connection.run_sync(HostIntegrityObservationRow.__table__.create, checkfirst=True)


class EndpointInventoryRepository:
    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal):
        self._session_factory = session_factory

    async def upsert_asset(self, asset: HostAssetRecord) -> tuple[HostAssetRecord, bool]:
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(EndpointAssetRow).where(
                    EndpointAssetRow.tenant_id == UUID(asset.tenant_id), EndpointAssetRow.agent_id == asset.agent_id
                )
            )
            if existing is None:
                row = EndpointAssetRow(
                    asset_id=asset.asset_id,
                    tenant_id=UUID(asset.tenant_id),
                    agent_id=asset.agent_id,
                    hostname=asset.hostname,
                    platform=asset.platform,
                    os_version=asset.os_version,
                    ip_addresses=asset.ip_addresses,
                    software=asset.software,
                    tags=asset.tags,
                    source=asset.source,
                    last_seen=asset.last_seen,
                    evidence=asset.evidence,
                )
                session.add(row)
                created = True
            else:
                row = existing
                row.hostname = asset.hostname
                row.platform = asset.platform
                row.os_version = asset.os_version
                row.ip_addresses = asset.ip_addresses
                row.software = asset.software
                row.tags = asset.tags
                row.source = asset.source
                row.last_seen = asset.last_seen
                row.evidence = asset.evidence
                created = False
            await session.commit()
            await session.refresh(row)
            return _asset_contract(row), created

    async def get_asset(self, tenant_id: str, asset_id: str) -> HostAssetRecord:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(EndpointAssetRow).where(
                    EndpointAssetRow.tenant_id == UUID(tenant_id), EndpointAssetRow.asset_id == asset_id
                )
            )
            if row is None:
                raise LookupError("Endpoint asset was not found for the authenticated tenant.")
            return _asset_contract(row)

    async def list_assets(self, tenant_id: str, limit: int = 200) -> list[HostAssetRecord]:
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(EndpointAssetRow)
                .where(EndpointAssetRow.tenant_id == UUID(tenant_id))
                .order_by(EndpointAssetRow.last_seen.desc())
                .limit(limit)
            )
            return [_asset_contract(row) for row in rows]

    async def persist_integrity(self, observation: IntegrityObservation) -> tuple[IntegrityObservation, bool]:
        if observation.automatic_enforcement:
            raise ValueError("Endpoint integrity ingestion never permits automatic enforcement.")
        async with self._session_factory() as session:
            asset = await session.scalar(
                select(EndpointAssetRow).where(
                    EndpointAssetRow.tenant_id == UUID(observation.tenant_id),
                    EndpointAssetRow.asset_id == observation.asset_id,
                )
            )
            if asset is None:
                raise LookupError("Integrity evidence references an unknown tenant-owned endpoint asset.")
            existing = await session.scalar(
                select(HostIntegrityObservationRow).where(
                    HostIntegrityObservationRow.tenant_id == UUID(observation.tenant_id),
                    HostIntegrityObservationRow.source == observation.source,
                    HostIntegrityObservationRow.source_event_id == observation.source_event_id,
                )
            )
            if existing is not None:
                return _integrity_contract(existing), False
            row = HostIntegrityObservationRow(
                observation_id=observation.observation_id,
                tenant_id=UUID(observation.tenant_id),
                asset_id=observation.asset_id,
                agent_id=observation.agent_id,
                source_event_id=observation.source_event_id,
                source=observation.source,
                check_type=observation.check_type,
                status=observation.status,
                severity=observation.severity,
                observed_at=observation.observed_at,
                path=observation.path,
                observed_hash=observation.observed_hash,
                expected_hash=observation.expected_hash,
                evidence=observation.evidence,
                automatic_enforcement=False,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _integrity_contract(row), True

    async def list_integrity(
        self, tenant_id: str, asset_id: Optional[str] = None, limit: int = 200
    ) -> list[IntegrityObservation]:
        statement = select(HostIntegrityObservationRow).where(HostIntegrityObservationRow.tenant_id == UUID(tenant_id))
        if asset_id:
            statement = statement.where(HostIntegrityObservationRow.asset_id == asset_id)
        statement = statement.order_by(HostIntegrityObservationRow.observed_at.desc()).limit(limit)
        async with self._session_factory() as session:
            rows = await session.scalars(statement)
            return [_integrity_contract(row) for row in rows]
