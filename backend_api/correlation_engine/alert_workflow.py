"""Governed analyst alert workflow derived from durable detection evidence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import AnalystAlertRow, AsyncSessionLocal, engine
from phantomnet_core.contracts import AlertRecord, DetectionRecord


SessionFactory = Callable[[], AsyncSession]
AlertStatus = Literal["new", "triaged", "in_progress", "resolved", "closed", "suppressed"]
SUPPRESSION_WINDOW_SECONDS = 900
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "new": {"triaged", "suppressed", "closed"},
    "triaged": {"in_progress", "resolved", "closed"},
    "in_progress": {"resolved", "closed"},
    "resolved": {"closed"},
    "suppressed": {"closed"},
    "closed": set(),
}


@dataclass(frozen=True)
class AlertWorkflowResult:
    alert: AlertRecord
    created: bool
    suppressed: bool


def governed_severity(detection: DetectionRecord) -> str:
    """Use a rule's already-governed severity without unreviewed ML escalation."""
    return detection.severity


def suppression_key_for(detection: DetectionRecord) -> str:
    """Create a stable tenant-local key for repeated evidence of the same governed rule."""
    fingerprint = str(detection.evidence.get("payload_fingerprint", ""))
    material = "|".join(
        [detection.tenant_id, detection.rule_id, detection.correlation_id or "", fingerprint]
    )
    return sha256(material.encode("utf-8")).hexdigest()


def suppression_window_for(detection: DetectionRecord, default_seconds: int = SUPPRESSION_WINDOW_SECONDS) -> int:
    """Honor a reviewed governed rule window only when its persisted evidence is bounded and well typed."""
    configured = detection.evidence.get("alert_suppression_window_seconds", default_seconds)
    if isinstance(configured, bool) or not isinstance(configured, int) or not 0 <= configured <= 86_400:
        return default_seconds
    return configured


def _to_contract(row: AnalystAlertRow) -> AlertRecord:
    return AlertRecord(
        alert_id=row.alert_id,
        tenant_id=str(row.tenant_id),
        detection_ids=list(row.detection_ids),
        correlation_id=row.correlation_id,
        title=row.title,
        severity=row.severity,
        status=row.status,
        first_seen=row.first_seen,
        last_seen=row.last_seen,
        occurrence_count=row.occurrence_count,
        suppression_key=row.suppression_key,
        suppressed_by_alert_id=row.suppressed_by_alert_id,
        mitre_evidence=list(row.mitre_evidence),
        evidence=dict(row.evidence),
        case_id=row.case_id,
        triaged_by=row.triaged_by,
    )


async def init_alert_workflow_store() -> None:
    """Create the alert workflow table when migrations have not already provisioned it."""
    async with engine.begin() as connection:
        await connection.run_sync(AnalystAlertRow.__table__.create, checkfirst=True)


class AlertWorkflow:
    """Create, suppress, retrieve, and transition analyst-facing alert state."""

    def __init__(
        self,
        session_factory: SessionFactory = AsyncSessionLocal,
        suppression_window_seconds: int = SUPPRESSION_WINDOW_SECONDS,
    ):
        self._session_factory = session_factory
        self._suppression_window_seconds = suppression_window_seconds

    async def ingest_detection(self, detection: DetectionRecord) -> AlertWorkflowResult:
        """Create one analyst alert or update the active alert suppressed by a repeat delivery."""
        now = detection.detected_at
        suppression_window_seconds = suppression_window_for(detection, self._suppression_window_seconds)
        cutoff = now - timedelta(seconds=suppression_window_seconds)
        suppression_key = suppression_key_for(detection)
        async with self._session_factory() as session:
            active_alert = await session.scalar(
                select(AnalystAlertRow)
                .where(
                    AnalystAlertRow.tenant_id == UUID(detection.tenant_id),
                    AnalystAlertRow.suppression_key == suppression_key,
                    AnalystAlertRow.status.in_(("new", "triaged", "in_progress")),
                    AnalystAlertRow.last_seen >= cutoff,
                )
                .order_by(AnalystAlertRow.last_seen.desc())
            )
            if active_alert is not None:
                if detection.detection_id in active_alert.detection_ids:
                    # At-least-once broker delivery may replay the same durable detection.
                    # Preserve the analyst record exactly rather than counting duplicate transport.
                    return AlertWorkflowResult(_to_contract(active_alert), created=False, suppressed=True)
                active_alert.detection_ids = [*active_alert.detection_ids, detection.detection_id]
                active_alert.last_seen = now
                active_alert.occurrence_count += 1
                await session.commit()
                # The committed state is fully derived from the active governed record
                # and this detection; no server-generated contract field needs refresh.
                return AlertWorkflowResult(_to_contract(active_alert), created=False, suppressed=True)

            alert = AlertRecord(
                tenant_id=detection.tenant_id,
                detection_ids=[detection.detection_id],
                correlation_id=detection.correlation_id,
                title=detection.title,
                severity=governed_severity(detection),
                status="new",
                first_seen=now,
                last_seen=now,
                suppression_key=suppression_key,
                mitre_evidence=detection.mitre_evidence,
                evidence={
                    "rule_id": detection.rule_id,
                    "rule_version": detection.rule_version,
                    "event_id": detection.event_id,
                    "detection_evidence": detection.evidence,
                    "suppression_window_seconds": suppression_window_seconds,
                },
            )
            row = AnalystAlertRow(
                alert_id=alert.alert_id,
                tenant_id=UUID(alert.tenant_id),
                detection_ids=alert.detection_ids,
                correlation_id=alert.correlation_id,
                title=alert.title,
                severity=alert.severity,
                status=alert.status,
                first_seen=alert.first_seen,
                last_seen=alert.last_seen,
                occurrence_count=alert.occurrence_count,
                suppression_key=alert.suppression_key,
                suppressed_by_alert_id=None,
                mitre_evidence=[evidence.model_dump(mode="json") for evidence in alert.mitre_evidence],
                evidence=alert.evidence,
                case_id=None,
                triaged_by=None,
            )
            session.add(row)
            await session.commit()
            # The alert contract contains only explicitly supplied governed fields, so
            # avoid a second read solely to hydrate a value we already own.
            return AlertWorkflowResult(_to_contract(row), created=True, suppressed=False)

    async def list_for_tenant(self, tenant_id: str, limit: int = 100) -> list[AlertRecord]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(AnalystAlertRow)
                .where(AnalystAlertRow.tenant_id == UUID(tenant_id))
                .order_by(AnalystAlertRow.last_seen.desc())
                .limit(safe_limit)
            )
            return [_to_contract(row) for row in rows]

    async def transition(
        self,
        tenant_id: str,
        alert_id: str,
        target_status: AlertStatus,
        actor: str,
        case_id: str | None = None,
    ) -> AlertRecord:
        """Apply a deliberate analyst workflow transition for one tenant-owned alert."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(AnalystAlertRow).where(
                    AnalystAlertRow.tenant_id == UUID(tenant_id),
                    AnalystAlertRow.alert_id == alert_id,
                )
            )
            if row is None:
                raise LookupError("Alert was not found for the authenticated tenant.")
            if target_status not in ALLOWED_TRANSITIONS[row.status]:
                raise ValueError(f"Invalid alert lifecycle transition from '{row.status}' to '{target_status}'.")
            row.status = target_status
            row.last_seen = datetime.now(timezone.utc)
            if target_status == "triaged":
                row.triaged_by = actor
            if case_id is not None:
                row.case_id = case_id
            await session.commit()
            await session.refresh(row)
            return _to_contract(row)
