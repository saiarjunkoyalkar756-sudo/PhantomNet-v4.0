"""Tenant-scoped, provenance-preserving evidence integration with no response authority."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import AsyncSessionLocal, IntegratedEvidenceRow, engine
from phantomnet_core.contracts import EventEnvelope, HostAssetRecord, IntegratedEvidenceRecord, IntegrityObservation


SessionFactory = Callable[[], AsyncSession]
EvidenceSourceKind = Literal["asset", "endpoint", "wazuh", "identity", "intelligence", "graph"]


def _contract(row: IntegratedEvidenceRow) -> IntegratedEvidenceRecord:
    return IntegratedEvidenceRecord(
        evidence_id=row.evidence_id,
        tenant_id=str(row.tenant_id),
        source_kind=row.source_kind,
        source_name=row.source_name,
        source_record_id=row.source_record_id,
        observed_at=row.observed_at,
        collected_at=row.collected_at,
        payload=dict(row.payload),
        tags=list(row.tags),
        provenance=dict(row.provenance),
        read_only=bool(row.read_only),
        automatic_enforcement=bool(row.automatic_enforcement),
    )


async def init_integrated_evidence_store() -> None:
    """Provision only the read-only integrated-evidence table when migrations are not yet applied."""
    async with engine.begin() as connection:
        await connection.run_sync(IntegratedEvidenceRow.__table__.create, checkfirst=True)


class IntegratedEvidenceRepository:
    """Persist and retrieve tenant-owned evidence without any response or mutation capability."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def persist(self, record: IntegratedEvidenceRecord) -> tuple[IntegratedEvidenceRecord, bool]:
        """Persist a read-only record once per tenant, source record, and payload fingerprint."""
        fingerprint = record.payload_fingerprint()
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(IntegratedEvidenceRow).where(
                    IntegratedEvidenceRow.tenant_id == UUID(record.tenant_id),
                    IntegratedEvidenceRow.source_kind == record.source_kind,
                    IntegratedEvidenceRow.source_name == record.source_name,
                    IntegratedEvidenceRow.source_record_id == record.source_record_id,
                    IntegratedEvidenceRow.payload_fingerprint == fingerprint,
                )
            )
            if existing is not None:
                return _contract(existing), False
            row = IntegratedEvidenceRow(
                evidence_id=record.evidence_id,
                tenant_id=UUID(record.tenant_id),
                source_kind=record.source_kind,
                source_name=record.source_name,
                source_record_id=record.source_record_id,
                observed_at=record.observed_at,
                collected_at=record.collected_at,
                payload=record.payload,
                tags=record.tags,
                provenance=record.provenance,
                payload_fingerprint=fingerprint,
                read_only=True,
                automatic_enforcement=False,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await session.scalar(
                    select(IntegratedEvidenceRow).where(
                        IntegratedEvidenceRow.tenant_id == UUID(record.tenant_id),
                        IntegratedEvidenceRow.source_kind == record.source_kind,
                        IntegratedEvidenceRow.source_name == record.source_name,
                        IntegratedEvidenceRow.source_record_id == record.source_record_id,
                        IntegratedEvidenceRow.payload_fingerprint == fingerprint,
                    )
                )
                if existing is None:
                    raise
                return _contract(existing), False
            await session.refresh(row)
            return _contract(row), True

    async def list_for_tenant(
        self,
        tenant_id: str,
        source_kind: EvidenceSourceKind | None = None,
        limit: int = 200,
    ) -> list[IntegratedEvidenceRecord]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            statement = (
                select(IntegratedEvidenceRow)
                .where(IntegratedEvidenceRow.tenant_id == UUID(tenant_id))
                .order_by(IntegratedEvidenceRow.observed_at.desc(), IntegratedEvidenceRow.evidence_id)
                .limit(safe_limit)
            )
            if source_kind is not None:
                statement = statement.where(IntegratedEvidenceRow.source_kind == source_kind)
            rows = await session.scalars(statement)
            return [_contract(row) for row in rows]

    async def get_for_tenant(self, tenant_id: str, evidence_id: str) -> IntegratedEvidenceRecord:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(IntegratedEvidenceRow).where(
                    IntegratedEvidenceRow.tenant_id == UUID(tenant_id),
                    IntegratedEvidenceRow.evidence_id == evidence_id,
                )
            )
            if row is None:
                raise LookupError("Integrated evidence was not found for the authenticated tenant.")
            return _contract(row)


@dataclass(frozen=True)
class IntegratedEvidenceOutcome:
    record: IntegratedEvidenceRecord
    created: bool
    event: EventEnvelope


class EvidenceIntegrationService:
    """Normalize trusted read-only source evidence into durable tenant-owned advisory context."""

    def __init__(self, repository: IntegratedEvidenceRepository | None = None) -> None:
        self._repository = repository or IntegratedEvidenceRepository()

    @staticmethod
    def project_event(record: IntegratedEvidenceRecord) -> EventEnvelope:
        """Project one durable evidence record into canonical telemetry without producing a detection or response."""
        return EventEnvelope(
            event_id=record.evidence_id,
            timestamp=record.observed_at,
            tenant_id=record.tenant_id,
            source="evidence-integration",
            event_type=f"EVIDENCE.{record.source_kind.upper()}.OBSERVED",
            severity="informational",
            correlation_id=record.source_record_id,
            payload={"evidence": record.model_dump(mode="json"), "automatic_enforcement": False},
            tags=["evidence", record.source_kind, *record.tags],
            provenance={
                "adapter": "evidence-integration",
                "source_name": record.source_name,
                "source_kind": record.source_kind,
                "source_record_id": record.source_record_id,
                "read_only": True,
            },
        )

    async def ingest(self, record: IntegratedEvidenceRecord) -> IntegratedEvidenceOutcome:
        stored, created = await self._repository.persist(record)
        return IntegratedEvidenceOutcome(record=stored, created=created, event=self.project_event(stored))

    async def list_for_tenant(
        self,
        tenant_id: str,
        source_kind: EvidenceSourceKind | None = None,
        limit: int = 200,
    ) -> list[IntegratedEvidenceRecord]:
        return await self._repository.list_for_tenant(tenant_id, source_kind=source_kind, limit=limit)

    async def get_for_tenant(self, tenant_id: str, evidence_id: str) -> IntegratedEvidenceRecord:
        return await self._repository.get_for_tenant(tenant_id, evidence_id)

    async def ingest_asset(self, asset: HostAssetRecord) -> IntegratedEvidenceOutcome:
        record = IntegratedEvidenceRecord(
            tenant_id=asset.tenant_id,
            source_kind="asset",
            source_name=asset.source,
            source_record_id=asset.asset_id,
            observed_at=asset.last_seen,
            payload={"asset": asset.model_dump(mode="json")},
            tags=["asset", "inventory", asset.source],
            provenance={"adapter": "endpoint-inventory", "upstream_adapter": asset.source, "read_only": True},
        )
        return await self.ingest(record)

    async def ingest_integrity(self, observation: IntegrityObservation) -> IntegratedEvidenceOutcome:
        source_kind: EvidenceSourceKind = "wazuh" if observation.source == "wazuh" else "endpoint"
        record = IntegratedEvidenceRecord(
            tenant_id=observation.tenant_id,
            source_kind=source_kind,
            source_name=observation.source,
            source_record_id=observation.source_event_id,
            observed_at=observation.observed_at,
            payload={"integrity": observation.model_dump(mode="json")},
            tags=["endpoint", "integrity", observation.check_type, observation.source],
            provenance={"adapter": "endpoint-inventory", "upstream_adapter": observation.source, "read_only": True},
        )
        return await self.ingest(record)

    async def ingest_intelligence(self, tenant_id: str, enrichment: Mapping[str, Any]) -> IntegratedEvidenceOutcome:
        """Persist only successful, explicitly read-only intelligence evidence; the caller owns any external retrieval."""
        evidence = enrichment.get("evidence")
        if enrichment.get("status") != "success" or not isinstance(evidence, Mapping):
            raise ValueError("Only successful read-only intelligence evidence can enter the integration layer.")
        provenance = evidence.get("provenance")
        provider = evidence.get("provider")
        indicator = evidence.get("indicator")
        if not isinstance(provenance, Mapping) or provenance.get("read_only") is not True:
            raise ValueError("Intelligence evidence must explicitly attest read_only provenance.")
        if not isinstance(provider, str) or not provider or not isinstance(indicator, str) or not indicator:
            raise ValueError("Intelligence evidence requires a provider and indicator identity.")
        record = IntegratedEvidenceRecord(
            tenant_id=tenant_id,
            source_kind="intelligence",
            source_name=provider,
            source_record_id=indicator,
            observed_at=datetime.now(timezone.utc),
            payload={"intelligence": dict(evidence)},
            tags=["intelligence", provider],
            provenance={**dict(provenance), "adapter": "evidence-integration", "read_only": True},
        )
        return await self.ingest(record)
