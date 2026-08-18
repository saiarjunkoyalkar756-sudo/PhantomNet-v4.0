"""Human-governed containment lifecycle with durable approvals, verification, rollback, and audit evidence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import os
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.audit_log_collector.integrity import GENESIS_HASH, append_record
from backend_api.shared.database import (
    AsyncSessionLocal,
    ContainmentApprovalRow,
    ContainmentAuditRecordRow,
    ContainmentExecutionRow,
    ContainmentRequestRow,
    engine,
)
from phantomnet_core.contracts import (
    ContainmentApproval,
    ContainmentExecutionEvidence,
    ContainmentRequest,
)


SessionFactory = Callable[[], AsyncSession]


class ContainmentAdapter(Protocol):
    name: str

    def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]: ...

    def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]: ...


class DisabledContainmentAdapter:
    name = "disabled"

    def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        return {
            "enforced": False,
            "verified": False,
            "rollback_available": False,
            "detail": "No endpoint containment adapter is configured; no action was executed.",
        }

    def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        return {
            "enforced": False,
            "verified": False,
            "detail": "No endpoint containment adapter is configured; no rollback was executed.",
        }


def _request_contract(row: ContainmentRequestRow) -> ContainmentRequest:
    return ContainmentRequest(
        request_id=row.request_id,
        tenant_id=str(row.tenant_id),
        action=row.action,
        target=row.target,
        asset_id=row.asset_id,
        playbook_id=row.playbook_id,
        requested_by=row.requested_by,
        requested_at=row.requested_at,
        status=row.status,
        idempotency_key=row.idempotency_key,
        parameters=dict(row.parameters),
        requires_approval=row.requires_approval,
        automatic_enforcement=bool(row.automatic_enforcement),
    )


def _approval_contract(row: ContainmentApprovalRow) -> ContainmentApproval:
    return ContainmentApproval(
        approval_id=row.approval_id,
        request_id=row.request_id,
        tenant_id=str(row.tenant_id),
        decision=row.decision,
        decided_by=row.decided_by,
        decided_at=row.decided_at,
        reason=row.reason,
    )


def _execution_contract(row: ContainmentExecutionRow) -> ContainmentExecutionEvidence:
    return ContainmentExecutionEvidence(
        execution_id=row.execution_id,
        request_id=row.request_id,
        tenant_id=str(row.tenant_id),
        approval_id=row.approval_id,
        adapter=row.adapter,
        status=row.status,
        executed_at=row.executed_at,
        verification=dict(row.verification),
        rollback_available=bool(row.rollback_available),
        rolled_back=bool(row.rolled_back),
        audit_record_hash=row.audit_record_hash,
    )


async def init_governed_containment_store() -> None:
    async with engine.begin() as connection:
        for table in (
            ContainmentRequestRow.__table__,
            ContainmentApprovalRow.__table__,
            ContainmentExecutionRow.__table__,
            ContainmentAuditRecordRow.__table__,
        ):
            await connection.run_sync(table.create, checkfirst=True)


class GovernedContainmentService:
    """Containment orchestration that fails closed without an explicit approval and evidence-producing adapter."""

    def __init__(
        self,
        session_factory: SessionFactory = AsyncSessionLocal,
        adapter: ContainmentAdapter | None = None,
        audit_signing_key: str | None = None,
        audit_key_id: str | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._adapter = adapter or DisabledContainmentAdapter()
        self._audit_signing_key = audit_signing_key if audit_signing_key is not None else os.getenv("PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY")
        self._audit_key_id = audit_key_id if audit_key_id is not None else os.getenv("PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID")

    async def _audit(self, tenant_id: str, actor_id: str | None, action: str, payload: dict[str, Any]) -> str:
        async with self._session_factory() as session:
            previous = await session.scalar(
                select(ContainmentAuditRecordRow.record_hash)
                .where(ContainmentAuditRecordRow.tenant_id == UUID(tenant_id))
                .order_by(ContainmentAuditRecordRow.id.desc())
                .limit(1)
            )
            record = append_record(
                record_id=f"containment:{payload.get('request_id', 'event')}:{datetime.now(timezone.utc).timestamp()}",
                actor_id=actor_id,
                action=action,
                payload=payload,
                previous_hash=previous or GENESIS_HASH,
                signing_key=self._audit_signing_key,
                signature_key_id=self._audit_key_id,
            )
            session.add(
                ContainmentAuditRecordRow(
                    tenant_id=UUID(tenant_id),
                    record_id=record.record_id,
                    timestamp=record.timestamp,
                    actor_id=record.actor_id,
                    action=record.action,
                    payload=record.payload,
                    previous_hash=record.previous_hash,
                    record_hash=record.record_hash,
                    signature=record.signature,
                    signature_key_id=record.signature_key_id,
                )
            )
            await session.commit()
            return record.record_hash

    def _require_signed_execution_audit(self) -> None:
        if not self._audit_signing_key or not self._audit_key_id:
            raise PermissionError("Containment execution requires configured HMAC-signed audit evidence.")

    async def request(self, request: ContainmentRequest) -> tuple[ContainmentRequest, bool]:
        if not request.requires_approval or request.automatic_enforcement:
            raise ValueError("High-impact containment requests must require approval and cannot be automatic.")
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(ContainmentRequestRow).where(
                    ContainmentRequestRow.tenant_id == UUID(request.tenant_id),
                    ContainmentRequestRow.idempotency_key == request.idempotency_key,
                )
            )
            if existing is not None:
                return _request_contract(existing), False
            row = ContainmentRequestRow(
                request_id=request.request_id,
                tenant_id=UUID(request.tenant_id),
                action=request.action,
                target=request.target,
                asset_id=request.asset_id,
                playbook_id=request.playbook_id,
                requested_by=request.requested_by,
                requested_at=request.requested_at,
                status="requested",
                idempotency_key=request.idempotency_key,
                parameters=request.parameters,
                requires_approval=True,
                automatic_enforcement=False,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
        await self._audit(request.tenant_id, request.requested_by, "containment.requested", {"request_id": request.request_id, "action": request.action, "target": request.target})
        return _request_contract(row), True

    async def approve(self, approval: ContainmentApproval) -> ContainmentApproval:
        async with self._session_factory() as session:
            request = await session.scalar(
                select(ContainmentRequestRow).where(
                    ContainmentRequestRow.tenant_id == UUID(approval.tenant_id),
                    ContainmentRequestRow.request_id == approval.request_id,
                )
            )
            if request is None:
                raise LookupError("Containment request was not found for the authenticated tenant.")
            if request.status != "requested":
                raise ValueError("Containment request is no longer awaiting an approval decision.")
            row = ContainmentApprovalRow(
                approval_id=approval.approval_id,
                request_id=approval.request_id,
                tenant_id=UUID(approval.tenant_id),
                decision=approval.decision,
                decided_by=approval.decided_by,
                decided_at=approval.decided_at,
                reason=approval.reason,
            )
            request.status = "approved" if approval.decision == "approved" else "rejected"
            session.add(row)
            await session.commit()
            await session.refresh(row)
        await self._audit(approval.tenant_id, approval.decided_by, f"containment.{approval.decision}", {"request_id": approval.request_id, "approval_id": approval.approval_id, "reason": approval.reason})
        return _approval_contract(row)

    async def execute(self, tenant_id: str, request_id: str, actor: str) -> ContainmentExecutionEvidence:
        self._require_signed_execution_audit()
        async with self._session_factory() as session:
            request_row = await session.scalar(select(ContainmentRequestRow).where(ContainmentRequestRow.tenant_id == UUID(tenant_id), ContainmentRequestRow.request_id == request_id))
            approval_row = await session.scalar(select(ContainmentApprovalRow).where(ContainmentApprovalRow.tenant_id == UUID(tenant_id), ContainmentApprovalRow.request_id == request_id))
            existing = await session.scalar(select(ContainmentExecutionRow).where(ContainmentExecutionRow.tenant_id == UUID(tenant_id), ContainmentExecutionRow.request_id == request_id))
            if existing is not None:
                return _execution_contract(existing)
            if request_row is None or approval_row is None or approval_row.decision != "approved" or request_row.status != "approved":
                raise PermissionError("Containment execution requires a recorded approved request.")
            request_row.status = "executing"
            await session.commit()
            request = _request_contract(request_row)
            approval = _approval_contract(approval_row)

        result = self._adapter.execute(request, approval)
        adapter_name = str(result.get("provider") or self._adapter.name)
        enforced = bool(result.get("enforced"))
        verified = bool(result.get("verified"))
        status = "verified" if enforced and verified else "failed"
        audit_hash = await self._audit(tenant_id, actor, "containment.executed", {"request_id": request_id, "approval_id": approval.approval_id, "adapter": adapter_name, "enforced": enforced, "verified": verified, "detail": result.get("detail", "")})
        evidence = ContainmentExecutionEvidence(
            request_id=request_id,
            tenant_id=tenant_id,
            approval_id=approval.approval_id,
            adapter=adapter_name,
            status=status,
            verification=result,
            rollback_available=bool(result.get("rollback_available")) and status == "verified",
            rolled_back=False,
            audit_record_hash=audit_hash,
        )
        async with self._session_factory() as session:
            request_row = await session.scalar(select(ContainmentRequestRow).where(ContainmentRequestRow.tenant_id == UUID(tenant_id), ContainmentRequestRow.request_id == request_id))
            row = ContainmentExecutionRow(
                execution_id=evidence.execution_id,
                request_id=request_id,
                tenant_id=UUID(tenant_id),
                approval_id=evidence.approval_id,
                adapter=evidence.adapter,
                status=evidence.status,
                executed_at=evidence.executed_at,
                verification=evidence.verification,
                rollback_available=evidence.rollback_available,
                rolled_back=False,
                audit_record_hash=audit_hash,
            )
            session.add(row)
            request_row.status = status
            await session.commit()
            await session.refresh(row)
            return _execution_contract(row)

    async def rollback(self, tenant_id: str, request_id: str, actor: str) -> ContainmentExecutionEvidence:
        self._require_signed_execution_audit()
        async with self._session_factory() as session:
            request_row = await session.scalar(select(ContainmentRequestRow).where(ContainmentRequestRow.tenant_id == UUID(tenant_id), ContainmentRequestRow.request_id == request_id))
            approval_row = await session.scalar(select(ContainmentApprovalRow).where(ContainmentApprovalRow.tenant_id == UUID(tenant_id), ContainmentApprovalRow.request_id == request_id))
            execution_row = await session.scalar(select(ContainmentExecutionRow).where(ContainmentExecutionRow.tenant_id == UUID(tenant_id), ContainmentExecutionRow.request_id == request_id))
            if request_row is None or approval_row is None or execution_row is None or execution_row.status != "verified" or not execution_row.rollback_available:
                raise PermissionError("Containment rollback requires a verified execution with rollback evidence.")
            request = _request_contract(request_row)
            approval = _approval_contract(approval_row)

        result = self._adapter.rollback(request, approval)
        adapter_name = str(result.get("provider") or self._adapter.name)
        verified = bool(result.get("verified"))
        audit_hash = await self._audit(tenant_id, actor, "containment.rolled_back", {"request_id": request_id, "approval_id": approval.approval_id, "adapter": adapter_name, "verified": verified, "detail": result.get("detail", "")})
        async with self._session_factory() as session:
            request_row = await session.scalar(select(ContainmentRequestRow).where(ContainmentRequestRow.tenant_id == UUID(tenant_id), ContainmentRequestRow.request_id == request_id))
            execution_row = await session.scalar(select(ContainmentExecutionRow).where(ContainmentExecutionRow.tenant_id == UUID(tenant_id), ContainmentExecutionRow.request_id == request_id))
            execution_row.status = "rolled_back" if verified else "failed"
            execution_row.rolled_back = verified
            execution_row.verification = {**execution_row.verification, "rollback": result}
            execution_row.audit_record_hash = audit_hash
            request_row.status = "rolled_back" if verified else "failed"
            await session.commit()
            await session.refresh(execution_row)
            return _execution_contract(execution_row)

    async def list_requests(self, tenant_id: str, limit: int = 200) -> list[ContainmentRequest]:
        async with self._session_factory() as session:
            rows = await session.scalars(select(ContainmentRequestRow).where(ContainmentRequestRow.tenant_id == UUID(tenant_id)).order_by(ContainmentRequestRow.requested_at.desc()).limit(limit))
            return [_request_contract(row) for row in rows]
