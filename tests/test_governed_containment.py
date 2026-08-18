from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.endpoint_containment_adapter import EndpointContainmentAdapter
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


TENANT_ID = "00000000-0000-0000-0000-000000000001"


class VerifiedAdapter:
    name = "verified-test-adapter"

    def execute(self, request, approval):
        return {"enforced": True, "verified": True, "rollback_available": True, "detail": "Endpoint isolated and verified."}

    def rollback(self, request, approval):
        return {"enforced": False, "verified": True, "detail": "Endpoint release verified."}


async def _isolated_service(adapter=None, signing_key="test-signing-key"):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    service = GovernedContainmentService(
        session_factory=sessions,
        adapter=adapter or VerifiedAdapter(),
        audit_signing_key=signing_key,
        audit_key_id="test-key" if signing_key else None,
    )
    return service, sessions, engine


def _request(idempotency_key="containment-idempotency-001"):
    return ContainmentRequest(
        tenant_id=TENANT_ID,
        action="isolate_endpoint",
        target="endpoint-001",
        asset_id="endpoint-001",
        requested_by="analyst-1",
        idempotency_key=idempotency_key,
        parameters={"reason": "validated high-confidence detection"},
        requires_approval=True,
        automatic_enforcement=False,
    )


@pytest.mark.asyncio
async def test_containment_requires_approval_then_records_hmac_audited_verified_execution_and_rollback():
    service, sessions, engine = await _isolated_service()
    try:
        request, created = await service.request(_request())
        duplicate, duplicate_created = await service.request(_request())
        assert created is True
        assert duplicate_created is False
        assert duplicate.request_id == request.request_id

        with pytest.raises(PermissionError, match="approved request"):
            await service.execute(TENANT_ID, request.request_id, "admin-1")

        approval = await service.approve(
            ContainmentApproval(
                request_id=request.request_id,
                tenant_id=TENANT_ID,
                decision="approved",
                decided_by="admin-1",
                reason="Scope and target checked against incident evidence.",
            )
        )
        execution = await service.execute(TENANT_ID, request.request_id, "admin-1")
        rollback = await service.rollback(TENANT_ID, request.request_id, "admin-1")

        assert approval.decision == "approved"
        assert execution.status == "verified"
        assert execution.rollback_available is True
        assert execution.audit_record_hash
        assert rollback.status == "rolled_back"
        assert rollback.rolled_back is True
        async with sessions() as session:
            audit_rows = list(await session.scalars(select(ContainmentAuditRecordRow).order_by(ContainmentAuditRecordRow.id)))
        assert [row.action for row in audit_rows] == ["containment.requested", "containment.approved", "containment.executed", "containment.rolled_back"]
        assert all(row.signature and row.signature_key_id == "test-key" for row in audit_rows)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_containment_execution_fails_closed_without_hmac_signing_configuration_or_verified_adapter_outcome():
    unsigned_service, _sessions, unsigned_engine = await _isolated_service(signing_key=None)
    disabled_service, _disabled_sessions, disabled_engine = await _isolated_service(adapter=type("Unverified", (), {"name": "unverified", "execute": lambda self, *_: {"enforced": True, "verified": False, "detail": "No verification"}, "rollback": lambda self, *_: {"verified": False}})())
    try:
        unsigned_request, _ = await unsigned_service.request(_request("containment-idempotency-002"))
        await unsigned_service.approve(ContainmentApproval(request_id=unsigned_request.request_id, tenant_id=TENANT_ID, decision="approved", decided_by="admin-1", reason="Approved for test."))
        with pytest.raises(PermissionError, match="HMAC-signed"):
            await unsigned_service.execute(TENANT_ID, unsigned_request.request_id, "admin-1")

        disabled_request, _ = await disabled_service.request(_request("containment-idempotency-003"))
        await disabled_service.approve(ContainmentApproval(request_id=disabled_request.request_id, tenant_id=TENANT_ID, decision="approved", decided_by="admin-1", reason="Approved for test."))
        failed = await disabled_service.execute(TENANT_ID, disabled_request.request_id, "admin-1")
        assert failed.status == "failed"
        assert failed.rollback_available is False
    finally:
        await unsigned_engine.dispose()
        await disabled_engine.dispose()


def test_endpoint_adapter_is_disabled_by_default_and_rejects_unallowlisted_targets_before_dispatch():
    request = _request()
    approval = ContainmentApproval(request_id=request.request_id, tenant_id=TENANT_ID, decision="approved", decided_by="admin-1", reason="Approved test.")
    disabled = EndpointContainmentAdapter()
    assert disabled.execute(request, approval)["enforced"] is False

    calls = []
    adapter = EndpointContainmentAdapter(
        enabled=True,
        allowed_tenants={TENANT_ID},
        allowed_assets={"other-endpoint"},
        dispatcher=lambda command: calls.append(command) or {"enforced": True, "verified": True},
    )
    rejected = adapter.execute(request, approval)
    assert rejected["enforced"] is False
    assert calls == []
