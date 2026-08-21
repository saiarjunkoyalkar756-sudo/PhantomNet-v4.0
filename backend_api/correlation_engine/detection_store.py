"""Durable repository for canonical detection records."""

from __future__ import annotations

from collections.abc import Callable
from typing import Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import AsyncSessionLocal, DetectionRecordRow, engine
from phantomnet_core.contracts import DetectionRecord


SessionFactory = Callable[[], AsyncSession]


def _to_contract(row: DetectionRecordRow) -> DetectionRecord:
    return DetectionRecord(
        detection_id=row.detection_id,
        detected_at=row.detected_at,
        rule_id=row.rule_id,
        rule_version=row.rule_version,
        event_id=row.event_id,
        tenant_id=str(row.tenant_id),
        correlation_id=row.correlation_id,
        severity=row.severity,
        title=row.title,
        status=row.status,
        evidence=row.evidence,
        mitre_evidence=list(row.mitre_evidence),
        tags=row.tags,
        automatic_enforcement=row.automatic_enforcement,
    )


async def init_detection_store() -> None:
    """Create the durable detection table when migrations have not already provisioned it."""
    async with engine.begin() as connection:
        await connection.run_sync(DetectionRecordRow.__table__.create, checkfirst=True)


class DetectionRepository:
    """Persist detection evidence with idempotency for at-least-once message delivery."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal):
        self._session_factory = session_factory

    async def persist(self, detection: DetectionRecord) -> Tuple[DetectionRecord, bool]:
        """Store one record and return ``(record, created)`` without duplicating delivery."""
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(DetectionRecordRow).where(DetectionRecordRow.detection_id == detection.detection_id)
            )
            if existing is not None:
                return _to_contract(existing), False

            row = DetectionRecordRow(
                detection_id=detection.detection_id,
                tenant_id=UUID(detection.tenant_id),
                event_id=detection.event_id,
                rule_id=detection.rule_id,
                rule_version=detection.rule_version,
                correlation_id=detection.correlation_id,
                severity=detection.severity,
                title=detection.title,
                status=detection.status,
                detected_at=detection.detected_at,
                evidence=detection.evidence,
                mitre_evidence=[evidence.model_dump(mode="json") for evidence in detection.mitre_evidence],
                tags=detection.tags,
                automatic_enforcement=detection.automatic_enforcement,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                duplicate = await session.scalar(
                    select(DetectionRecordRow).where(
                        DetectionRecordRow.tenant_id == UUID(detection.tenant_id),
                        DetectionRecordRow.event_id == detection.event_id,
                        DetectionRecordRow.rule_id == detection.rule_id,
                    )
                )
                if duplicate is None:
                    raise
                return _to_contract(duplicate), False
            # All fields exposed by the contract are explicit governed inputs. With
            # expire_on_commit=False, no post-commit refresh round trip is required.
            return _to_contract(row), True

    async def get_for_tenant(self, tenant_id: str, detection_id: str) -> DetectionRecord:
        """Return one durable governed detection for its owning tenant only."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(DetectionRecordRow).where(
                    DetectionRecordRow.tenant_id == UUID(tenant_id),
                    DetectionRecordRow.detection_id == detection_id,
                )
            )
            if row is None:
                raise LookupError("Detection was not found for the authenticated tenant.")
            return _to_contract(row)

    async def list_for_tenant(self, tenant_id: str, limit: int = 100) -> list[DetectionRecord]:
        """Return newest durable detections for one tenant only."""
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(DetectionRecordRow)
                .where(DetectionRecordRow.tenant_id == UUID(tenant_id))
                .order_by(DetectionRecordRow.detected_at.desc())
                .limit(safe_limit)
            )
            return [_to_contract(row) for row in rows]
