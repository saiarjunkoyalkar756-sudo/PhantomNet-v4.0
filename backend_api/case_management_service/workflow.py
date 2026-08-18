"""Governed analyst case and playbook lifecycle management."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AnalystAlertRow,
    AsyncSessionLocal,
    CasePlaybookRunRow,
    InvestigationCaseRow,
    engine,
)
from phantomnet_core.contracts import CaseRecord, PlaybookRunRecord


SessionFactory = Callable[[], AsyncSession]
CaseStatus = Literal["new", "triaged", "in_progress", "resolved", "closed"]
PlaybookStatus = Literal[
    "requested", "awaiting_approval", "approved", "running", "completed", "failed", "cancelled"
]
CASE_TRANSITIONS: dict[str, set[str]] = {
    "new": {"triaged", "in_progress", "closed"},
    "triaged": {"in_progress", "resolved", "closed"},
    "in_progress": {"resolved", "closed"},
    "resolved": {"closed"},
    "closed": set(),
}
PLAYBOOK_TRANSITIONS: dict[str, set[str]] = {
    "requested": {"awaiting_approval", "approved", "cancelled"},
    "awaiting_approval": {"approved", "cancelled"},
    "approved": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


def _case_contract(row: InvestigationCaseRow) -> CaseRecord:
    return CaseRecord(
        case_id=row.case_id,
        tenant_id=str(row.tenant_id),
        alert_ids=list(row.alert_ids),
        title=row.title,
        severity=row.severity,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        created_by=row.created_by,
        assigned_to=row.assigned_to,
        evidence=dict(row.evidence),
        timeline=list(row.timeline),
    )


def _run_contract(row: CasePlaybookRunRow) -> PlaybookRunRecord:
    return PlaybookRunRecord(
        run_id=row.run_id,
        tenant_id=str(row.tenant_id),
        case_id=row.case_id,
        playbook_id=row.playbook_id,
        playbook_version=row.playbook_version,
        status=row.status,
        requires_approval=row.requires_approval,
        requested_by=row.requested_by,
        approved_by=row.approved_by,
        requested_at=row.requested_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        evidence=dict(row.evidence),
    )


async def init_case_workflow_store() -> None:
    """Provision the governed case lifecycle tables where migrations have not run."""
    async with engine.begin() as connection:
        await connection.run_sync(InvestigationCaseRow.__table__.create, checkfirst=True)
        await connection.run_sync(CasePlaybookRunRow.__table__.create, checkfirst=True)


class CaseWorkflow:
    """Link alerts to durable cases and track playbook workflow state only."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal):
        self._session_factory = session_factory

    async def create_from_alert(self, tenant_id: str, alert_id: str, actor: str) -> tuple[CaseRecord, bool]:
        """Create one case from a tenant-owned alert, or return its existing linked case."""
        async with self._session_factory() as session:
            alert = await session.scalar(
                select(AnalystAlertRow).where(
                    AnalystAlertRow.tenant_id == UUID(tenant_id), AnalystAlertRow.alert_id == alert_id
                )
            )
            if alert is None:
                raise LookupError("Alert was not found for the authenticated tenant.")
            if alert.case_id:
                existing = await session.scalar(
                    select(InvestigationCaseRow).where(
                        InvestigationCaseRow.tenant_id == UUID(tenant_id),
                        InvestigationCaseRow.case_id == alert.case_id,
                    )
                )
                if existing is not None:
                    return _case_contract(existing), False

            now = datetime.now(timezone.utc)
            case = CaseRecord(
                tenant_id=tenant_id,
                alert_ids=[alert.alert_id],
                title=f"Investigation: {alert.title}",
                severity=alert.severity,
                status="triaged" if alert.status in {"new", "triaged"} else "in_progress",
                created_by=actor,
                evidence={
                    "alert_id": alert.alert_id,
                    "detection_ids": list(alert.detection_ids),
                    "mitre_evidence": list(alert.mitre_evidence),
                    "alert_evidence": dict(alert.evidence),
                },
                timeline=[
                    {
                        "at": now.isoformat(),
                        "actor": actor,
                        "action": "case_created_from_alert",
                        "alert_id": alert.alert_id,
                    }
                ],
            )
            row = InvestigationCaseRow(
                case_id=case.case_id,
                tenant_id=UUID(case.tenant_id),
                alert_ids=case.alert_ids,
                title=case.title,
                severity=case.severity,
                status=case.status,
                created_at=case.created_at,
                updated_at=case.updated_at,
                created_by=case.created_by,
                assigned_to=None,
                evidence=case.evidence,
                timeline=case.timeline,
            )
            session.add(row)
            alert.case_id = case.case_id
            if alert.status == "new":
                alert.status = "triaged"
                alert.triaged_by = actor
            await session.commit()
            await session.refresh(row)
            return _case_contract(row), True

    async def get_case(self, tenant_id: str, case_id: str) -> CaseRecord:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(InvestigationCaseRow).where(
                    InvestigationCaseRow.tenant_id == UUID(tenant_id), InvestigationCaseRow.case_id == case_id
                )
            )
            if row is None:
                raise LookupError("Case was not found for the authenticated tenant.")
            return _case_contract(row)

    async def transition_case(self, tenant_id: str, case_id: str, target_status: CaseStatus, actor: str) -> CaseRecord:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(InvestigationCaseRow).where(
                    InvestigationCaseRow.tenant_id == UUID(tenant_id), InvestigationCaseRow.case_id == case_id
                )
            )
            if row is None:
                raise LookupError("Case was not found for the authenticated tenant.")
            if target_status not in CASE_TRANSITIONS[row.status]:
                raise ValueError(f"Invalid case lifecycle transition from '{row.status}' to '{target_status}'.")
            now = datetime.now(timezone.utc)
            row.status = target_status
            row.updated_at = now
            row.timeline = [
                *row.timeline,
                {"at": now.isoformat(), "actor": actor, "action": "case_status_changed", "status": target_status},
            ]
            await session.commit()
            await session.refresh(row)
            return _case_contract(row)

    async def request_playbook(
        self,
        tenant_id: str,
        case_id: str,
        playbook_id: str,
        playbook_version: str,
        actor: str,
        requires_approval: bool = True,
    ) -> PlaybookRunRecord:
        """Record a case-bound playbook request; this function does not execute any step."""
        await self.get_case(tenant_id, case_id)
        status: PlaybookStatus = "awaiting_approval" if requires_approval else "approved"
        run = PlaybookRunRecord(
            tenant_id=tenant_id,
            case_id=case_id,
            playbook_id=playbook_id,
            playbook_version=playbook_version,
            status=status,
            requires_approval=requires_approval,
            requested_by=actor,
            evidence={"execution_dispatched": False, "case_id": case_id},
        )
        async with self._session_factory() as session:
            case_row = await session.scalar(
                select(InvestigationCaseRow).where(
                    InvestigationCaseRow.tenant_id == UUID(tenant_id), InvestigationCaseRow.case_id == case_id
                )
            )
            if case_row is None:
                raise LookupError("Case was not found for the authenticated tenant.")
            row = CasePlaybookRunRow(
                run_id=run.run_id,
                tenant_id=UUID(run.tenant_id),
                case_id=run.case_id,
                playbook_id=run.playbook_id,
                playbook_version=run.playbook_version,
                status=run.status,
                requires_approval=run.requires_approval,
                requested_by=run.requested_by,
                approved_by=None,
                requested_at=run.requested_at,
                started_at=None,
                completed_at=None,
                evidence=run.evidence,
            )
            session.add(row)
            case_row.updated_at = run.requested_at
            case_row.timeline = [
                *case_row.timeline,
                {
                    "at": run.requested_at.isoformat(),
                    "actor": actor,
                    "action": "playbook_requested",
                    "run_id": run.run_id,
                    "playbook_id": playbook_id,
                    "status": status,
                },
            ]
            await session.commit()
            await session.refresh(row)
            return _run_contract(row)

    async def transition_playbook(
        self,
        tenant_id: str,
        run_id: str,
        target_status: PlaybookStatus,
        actor: str,
    ) -> PlaybookRunRecord:
        """Record a governed playbook lifecycle transition without dispatching playbook actions."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(CasePlaybookRunRow).where(
                    CasePlaybookRunRow.tenant_id == UUID(tenant_id), CasePlaybookRunRow.run_id == run_id
                )
            )
            if row is None:
                raise LookupError("Playbook run was not found for the authenticated tenant.")
            if target_status not in PLAYBOOK_TRANSITIONS[row.status]:
                raise ValueError(f"Invalid playbook lifecycle transition from '{row.status}' to '{target_status}'.")
            if target_status == "approved" and row.requires_approval:
                row.approved_by = actor
            now = datetime.now(timezone.utc)
            if target_status == "running":
                row.started_at = now
            if target_status in {"completed", "failed", "cancelled"}:
                row.completed_at = now
            row.status = target_status
            row.evidence = {**row.evidence, "execution_dispatched": False, "last_transition_by": actor}
            case_row = await session.scalar(
                select(InvestigationCaseRow).where(
                    InvestigationCaseRow.tenant_id == UUID(tenant_id), InvestigationCaseRow.case_id == row.case_id
                )
            )
            if case_row is None:
                raise LookupError("Linked case was not found for the authenticated tenant.")
            case_row.updated_at = now
            case_row.timeline = [
                *case_row.timeline,
                {
                    "at": now.isoformat(),
                    "actor": actor,
                    "action": "playbook_status_changed",
                    "run_id": row.run_id,
                    "status": target_status,
                    "execution_dispatched": False,
                },
            ]
            await session.commit()
            await session.refresh(row)
            return _run_contract(row)

    async def list_playbook_runs(self, tenant_id: str, case_id: str) -> list[PlaybookRunRecord]:
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(CasePlaybookRunRow)
                .where(CasePlaybookRunRow.tenant_id == UUID(tenant_id), CasePlaybookRunRow.case_id == case_id)
                .order_by(CasePlaybookRunRow.requested_at.desc())
            )
            return [_run_contract(row) for row in rows]

    async def list_cases(self, tenant_id: str, limit: int = 100) -> list[CaseRecord]:
        """Return the newest tenant-owned governed cases for read-only graph projection."""
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(InvestigationCaseRow)
                .where(InvestigationCaseRow.tenant_id == UUID(tenant_id))
                .order_by(InvestigationCaseRow.updated_at.desc())
                .limit(safe_limit)
            )
            return [_case_contract(row) for row in rows]
