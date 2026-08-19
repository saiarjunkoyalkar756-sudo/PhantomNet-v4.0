"""Stress coverage for the governed containment lifecycle using a deterministic non-live adapter."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.audit_log_collector.integrity import verify_chain
from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


TENANT_ID = "00000000-0000-0000-0000-000000000001"
LIFECYCLE_COUNT = 24


class DeterministicVerifiedAdapter:
    """Records simulated adapter calls while returning evidence shaped like a real adapter result."""

    name = "deterministic-stress-adapter"

    def __init__(self) -> None:
        self.execute_calls: list[str] = []
        self.rollback_calls: list[str] = []

    def execute(self, request: ContainmentRequest, _approval: ContainmentApproval) -> dict[str, object]:
        self.execute_calls.append(request.request_id)
        return {
            "enforced": True,
            "verified": True,
            "rollback_available": True,
            "detail": "Controlled adapter acknowledged and verified endpoint isolation.",
        }

    def rollback(self, request: ContainmentRequest, _approval: ContainmentApproval) -> dict[str, object]:
        self.rollback_calls.append(request.request_id)
        return {
            "enforced": False,
            "verified": True,
            "detail": "Controlled adapter acknowledged and verified endpoint release.",
        }


async def _service() -> tuple[GovernedContainmentService, DeterministicVerifiedAdapter, object, object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    adapter = DeterministicVerifiedAdapter()
    service = GovernedContainmentService(
        session_factory=sessions,
        adapter=adapter,
        audit_signing_key="governed-lifecycle-stress-key",
        audit_key_id="governed-lifecycle-stress-key-id",
    )
    return service, adapter, sessions, engine


def _request(index: int) -> ContainmentRequest:
    return ContainmentRequest(
        tenant_id=TENANT_ID,
        action="isolate_endpoint",
        target=f"controlled-endpoint-{index:02d}",
        asset_id=f"controlled-endpoint-{index:02d}",
        requested_by="stress-analyst",
        idempotency_key=f"governed-lifecycle-stress-{index:02d}",
        parameters={"exercise": "approved-lifecycle-stress", "index": index},
        requires_approval=True,
        automatic_enforcement=False,
    )


async def test_governed_containment_stress_preserves_signed_lifecycle_evidence_for_every_verified_rollback():
    service, adapter, sessions, engine = await _service()
    try:
        request_ids: list[str] = []
        for index in range(LIFECYCLE_COUNT):
            request, created = await service.request(_request(index))
            request_ids.append(request.request_id)
            assert created is True

            approval = await service.approve(
                ContainmentApproval(
                    request_id=request.request_id,
                    tenant_id=TENANT_ID,
                    decision="approved",
                    decided_by="stress-approver",
                    reason="Controlled lifecycle stress validation with scoped synthetic endpoint.",
                )
            )
            execution = await service.execute(TENANT_ID, request.request_id, "stress-approver")
            rollback = await service.rollback(TENANT_ID, request.request_id, "stress-approver")

            assert approval.decision == "approved"
            assert execution.status == "verified"
            assert execution.rollback_available is True
            assert rollback.status == "rolled_back"
            assert rollback.rolled_back is True

        assert adapter.execute_calls == request_ids
        assert adapter.rollback_calls == request_ids

        async with sessions() as session:
            rows = list(
                await session.scalars(
                    select(ContainmentAuditRecordRow)
                    .where(ContainmentAuditRecordRow.tenant_id == TENANT_ID)
                    .order_by(ContainmentAuditRecordRow.id)
                )
            )
        records = [
            {
                "record_id": row.record_id,
                "timestamp": row.timestamp,
                "actor_id": row.actor_id,
                "action": row.action,
                "payload": row.payload,
                "previous_hash": row.previous_hash,
                "record_hash": row.record_hash,
                "signature": row.signature,
                "signature_key_id": row.signature_key_id,
            }
            for row in rows
        ]
        assert len(records) == LIFECYCLE_COUNT * 4
        assert verify_chain(
            records,
            signing_key="governed-lifecycle-stress-key",
            require_signature=True,
            expected_key_id="governed-lifecycle-stress-key-id",
        )
    finally:
        await engine.dispose()
