"""API routes for the human-governed containment lifecycle."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_api.audit_log_collector.verification import ContainmentAuditVerifier
from backend_api.core.response import success_response
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.response_adapter_router import GovernedResponseAdapterRouter
from backend_api.soar_engine.wazuh_response_receipts import WazuhResponseReceipt, WazuhResponseReceiptService
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


router = APIRouter(prefix="/governed-containment", tags=["Governed Containment"])
containment_service = GovernedContainmentService(adapter=GovernedResponseAdapterRouter())
audit_verifier = ContainmentAuditVerifier()
wazuh_response_receipt_service = WazuhResponseReceiptService()


class ContainmentRequestCreate(BaseModel):
    action: str
    target: str = Field(min_length=1, max_length=255)
    asset_id: Optional[str] = None
    playbook_id: Optional[str] = None
    idempotency_key: str = Field(min_length=16, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecisionCreate(BaseModel):
    decision: str
    reason: str = Field(min_length=3, max_length=500)


@router.post("/requests", status_code=201)
async def create_containment_request(
    request: ContainmentRequestCreate,
    current_user: User = Depends(require_capability("response:request")),
):
    try:
        containment, created = await containment_service.request(
            ContainmentRequest(
                tenant_id=str(current_user.tenant_id),
                action=request.action,
                target=request.target,
                asset_id=request.asset_id,
                playbook_id=request.playbook_id,
                requested_by=current_user.username,
                idempotency_key=request.idempotency_key,
                parameters=request.parameters,
                requires_approval=True,
                automatic_enforcement=False,
            )
        )
    except PermissionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data={"request": containment.model_dump(mode="json"), "created": created})


@router.post("/requests/{request_id}/decision")
async def decide_containment_request(
    request_id: str,
    decision: ApprovalDecisionCreate,
    current_user: User = Depends(require_capability("response:approve")),
):
    if decision.decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be approved or rejected.")
    try:
        approval = await containment_service.approve(
            ContainmentApproval(
                request_id=request_id,
                tenant_id=str(current_user.tenant_id),
                decision=decision.decision,
                decided_by=current_user.username,
                reason=decision.reason,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Containment request not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return success_response(data=approval.model_dump(mode="json"))


@router.get("/requests/{request_id}/preflight")
async def preflight_containment_request(
    request_id: str,
    current_user: User = Depends(require_capability("response:approve")),
):
    """Return readiness only; this route never contacts an adapter, creates approval, or dispatches containment."""
    try:
        readiness = await containment_service.preflight(str(current_user.tenant_id), request_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Containment request not found.") from exc
    return success_response(data=readiness)


@router.post("/requests/{request_id}/execute")
async def execute_containment_request(
    request_id: str,
    current_user: User = Depends(require_capability("response:approve")),
):
    try:
        evidence = await containment_service.execute(str(current_user.tenant_id), request_id, current_user.username)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Containment request not found.") from exc
    return success_response(data=evidence.model_dump(mode="json"))


@router.post("/requests/{request_id}/rollback")
async def rollback_containment_request(
    request_id: str,
    current_user: User = Depends(require_capability("response:approve")),
):
    try:
        evidence = await containment_service.rollback(str(current_user.tenant_id), request_id, current_user.username)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return success_response(data=evidence.model_dump(mode="json"))


@router.post("/wazuh/receipts", status_code=202)
async def record_wazuh_response_receipt(receipt: WazuhResponseReceipt):
    """Accept only a fresh HMAC-signed endpoint receipt; this route cannot create approvals or commands."""
    try:
        stored = await wazuh_response_receipt_service.submit(receipt)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return success_response(
        data={
            "receipt_id": stored.receipt_id,
            "request_id": stored.request_id,
            "accepted": True,
            "automatic_enforcement": False,
        }
    )


@router.get("/audit/verify")
async def verify_containment_audit_chain(
    current_user: User = Depends(require_capability("audit:read")),
):
    """Verify only the authenticated tenant's HMAC-signed containment audit chain."""
    signing_key = os.getenv("PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY")
    key_id = os.getenv("PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID")
    if not signing_key or not key_id:
        raise HTTPException(status_code=503, detail="Signed audit verification is not configured.")
    verification = await audit_verifier.verify_tenant(
        str(current_user.tenant_id),
        signing_key=signing_key,
        require_signature=True,
        expected_key_id=key_id,
    )
    return success_response(data={
        "tenant_id": verification.tenant_id,
        "record_count": verification.record_count,
        "valid": verification.valid,
        "require_signature": verification.require_signature,
        "expected_key_id": verification.expected_key_id,
    })


@router.get("/requests")
async def list_containment_requests(
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("audit:read")),
):
    requests = await containment_service.list_requests(str(current_user.tenant_id), limit=limit)
    return success_response(data=[request.model_dump(mode="json") for request in requests])
