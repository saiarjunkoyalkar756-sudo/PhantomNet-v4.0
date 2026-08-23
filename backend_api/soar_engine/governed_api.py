"""API routes for the human-governed containment lifecycle."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend_api.ai_behavioral_engine.advisory_model import (
    AdvisoryModelAssessmentRepository,
    AdvisoryModelAssessmentService,
    DeterministicAdvisoryProvider,
)
from backend_api.ai_behavioral_engine.defensive_evaluation import (
    DefensiveEvaluationRepository,
    DefensiveModelEvaluationService,
    RiskScoreThresholdClassifier,
    build_dataset_version,
)
from backend_api.audit_log_collector.verification import ContainmentAuditVerifier
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.evidence_vault.integration import EvidenceIntegrationService
from backend_api.core.response import success_response
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from backend_api.telemetry_ingestor.signed_auth import TelemetryCredentialRepository
from backend_api.soar_engine.autonomous_defense import (
    AutonomousDefenseDecisionService,
    AutonomousDefenseRepository,
)
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.response_adapter_router import GovernedResponseAdapterRouter
from backend_api.soar_engine.wazuh_response_receipts import WazuhResponseReceipt, WazuhResponseReceiptService
from phantomnet_core.contracts import (
    AutonomousDefensePolicy,
    ContainmentApproval,
    ContainmentRequest,
    DefensiveDatasetSample,
    DefensiveDatasetSource,
    DefensiveEvaluationPolicy,
    TelemetrySigningCredential,
)


router = APIRouter(prefix="/governed-containment", tags=["Governed Containment"])
containment_service = GovernedContainmentService(adapter=GovernedResponseAdapterRouter())
audit_verifier = ContainmentAuditVerifier()
wazuh_response_receipt_service = WazuhResponseReceiptService()
autonomous_defense_repository = AutonomousDefenseRepository()
autonomous_defense_service = AutonomousDefenseDecisionService(
    autonomous_defense_repository,
    EvidenceIntegrationService(),
    containment_service,
)
detection_repository = DetectionRepository()
defensive_evaluation_repository = DefensiveEvaluationRepository()
defensive_evaluation_service = DefensiveModelEvaluationService(defensive_evaluation_repository)
advisory_assessment_repository = AdvisoryModelAssessmentRepository()
telemetry_credential_repository = TelemetryCredentialRepository()
deterministic_advisory_provider = DeterministicAdvisoryProvider()
advisory_assessment_service = AdvisoryModelAssessmentService(
    defensive_evaluation_repository,
    advisory_assessment_repository,
    deterministic_advisory_provider,
)
evidence_integration_service = EvidenceIntegrationService()


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


class AutonomousDefenseEvaluationRequest(BaseModel):
    detection_id: str = Field(min_length=1, max_length=255)


class TelemetryCredentialCreate(BaseModel):
    agent_id: str = Field(min_length=3, max_length=128)
    key_id: str = Field(min_length=8, max_length=128)
    public_key_pem: str = Field(min_length=128, max_length=8192)

    def to_contract(self, tenant_id: str) -> TelemetrySigningCredential:
        return TelemetrySigningCredential(
            tenant_id=tenant_id,
            agent_id=self.agent_id,
            key_id=self.key_id,
            public_key_pem=self.public_key_pem,
            status="active",
        )


def _telemetry_credential_metadata(credential: TelemetrySigningCredential) -> dict[str, Any]:
    """Return public operational metadata only; key material is never echoed by governed APIs."""
    return {
        "credential_id": credential.credential_id,
        "tenant_id": credential.tenant_id,
        "agent_id": credential.agent_id,
        "key_id": credential.key_id,
        "status": credential.status,
        "created_at": credential.created_at,
        "revoked_at": credential.revoked_at,
    }


class DefensiveDatasetSourceCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    source_type: str
    source_uri: Optional[str] = Field(default=None, max_length=1024)
    source_fingerprint: str = Field(min_length=64, max_length=64)
    license_reference: Optional[str] = Field(default=None, max_length=1024)
    operator_approved: bool = False
    license_reviewed: bool = False

    def to_contract(self, tenant_id: str, approved_by: str) -> DefensiveDatasetSource:
        approved_at = datetime.now(timezone.utc) if self.operator_approved else None
        return DefensiveDatasetSource(
            tenant_id=tenant_id,
            name=self.name,
            source_type=self.source_type,
            source_uri=self.source_uri,
            source_fingerprint=self.source_fingerprint,
            license_reference=self.license_reference,
            operator_approved=self.operator_approved,
            license_reviewed=self.license_reviewed,
            contains_raw_telemetry=False,
            sanitization_attested=True,
            approved_by=approved_by if self.operator_approved else None,
            approved_at=approved_at,
            automatic_enforcement=False,
        )


class DefensiveDatasetSampleCreate(BaseModel):
    split: str
    label: str
    attack_family: Optional[str] = Field(default=None, min_length=2, max_length=100)
    mitre_techniques: list[str] = Field(default_factory=list, max_length=16)
    feature_payload: Dict[str, Any] = Field(default_factory=dict)
    source_record_fingerprint: str = Field(min_length=64, max_length=64)

    def to_contract(self, tenant_id: str, dataset_id: str) -> DefensiveDatasetSample:
        return DefensiveDatasetSample(
            tenant_id=tenant_id,
            dataset_id=dataset_id,
            split=self.split,
            label=self.label,
            attack_family=self.attack_family,
            mitre_techniques=self.mitre_techniques,
            feature_payload=self.feature_payload,
            source_record_fingerprint=self.source_record_fingerprint,
            sanitized=True,
            automatic_enforcement=False,
        )


class DefensiveDatasetCreate(BaseModel):
    source_id: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=3, max_length=160)
    version: str = Field(min_length=3, max_length=40)
    intended_use: str = "evaluation_only"
    samples: list[DefensiveDatasetSampleCreate] = Field(min_length=1, max_length=10_000)


class DefensiveEvaluationPolicyCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    enabled: bool = True
    minimum_precision: float = Field(default=0.80, ge=0.50, le=1.0)
    minimum_recall: float = Field(default=0.80, ge=0.50, le=1.0)
    maximum_false_positive_rate: float = Field(default=0.10, ge=0.0, le=0.50)
    minimum_attack_samples: int = Field(default=5, ge=1, le=1_000_000)
    minimum_benign_samples: int = Field(default=5, ge=1, le=1_000_000)
    require_test_split: bool = True

    def to_contract(self, tenant_id: str) -> DefensiveEvaluationPolicy:
        return DefensiveEvaluationPolicy(tenant_id=tenant_id, **self.model_dump())


class DefensiveEvaluationRunRequest(BaseModel):
    policy_id: str = Field(min_length=1, max_length=255)
    dataset_id: str = Field(min_length=1, max_length=255)


class AdvisoryAssessmentRequest(BaseModel):
    detection_id: str = Field(min_length=1, max_length=255)
    evaluation_id: str = Field(min_length=1, max_length=255)


class AutonomousDefensePolicyCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    enabled: bool = True
    trigger_rule_ids: list[str] = Field(default_factory=list, max_length=32)
    minimum_severity: str = "high"
    decision_mode: str = "investigate"
    minimum_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    minimum_evidence_count: int = Field(default=1, ge=1, le=16)
    required_evidence_kinds: list[str] = Field(default_factory=list, max_length=6)
    cooldown_seconds: int = Field(default=300, ge=60, le=86_400)
    max_decisions_per_hour: int = Field(default=12, ge=1, le=120)
    containment_action: Optional[str] = None
    target: Optional[str] = Field(default=None, min_length=1, max_length=255)
    asset_id: Optional[str] = Field(default=None, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    def to_contract(self, tenant_id: str) -> AutonomousDefensePolicy:
        return AutonomousDefensePolicy(tenant_id=tenant_id, **self.model_dump())


@router.post("/telemetry-credentials")
async def register_telemetry_credential(
    request: TelemetryCredentialCreate,
    current_user: User = Depends(require_capability("agents:approve")),
):
    """Register an active public key for one authenticated tenant's agent telemetry only."""
    try:
        credential, created = await telemetry_credential_repository.register(
            request.to_contract(str(current_user.tenant_id))
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Telemetry credential was rejected.") from exc
    return success_response(data={"credential": _telemetry_credential_metadata(credential), "created": created})


@router.get("/telemetry-credentials")
async def list_telemetry_credentials(
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("audit:read")),
):
    credentials = await telemetry_credential_repository.list_for_tenant(str(current_user.tenant_id), limit=limit)
    return success_response(data=[_telemetry_credential_metadata(credential) for credential in credentials])


@router.post("/telemetry-credentials/{credential_id}/revoke")
async def revoke_telemetry_credential(
    credential_id: str,
    current_user: User = Depends(require_capability("agents:approve")),
):
    try:
        credential = await telemetry_credential_repository.revoke(str(current_user.tenant_id), credential_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Telemetry credential was not found.") from exc
    return success_response(data=_telemetry_credential_metadata(credential))


@router.post("/defensive-data/sources", status_code=201)
async def register_defensive_dataset_source(
    source: DefensiveDatasetSourceCreate,
    current_user: User = Depends(require_capability("response:approve")),
):
    """Register only approved, sanitized source provenance; raw telemetry cannot enter this API."""
    try:
        stored, created = await defensive_evaluation_repository.register_source(
            source.to_contract(str(current_user.tenant_id), current_user.username)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data={"source": stored.model_dump(mode="json"), "created": created})


@router.post("/defensive-data/datasets", status_code=201)
async def register_defensive_dataset(
    dataset: DefensiveDatasetCreate,
    current_user: User = Depends(require_capability("response:approve")),
):
    """Register a versioned corpus of minimized labelled features; raw event uploads are unsupported."""
    tenant_id = str(current_user.tenant_id)
    dataset_id = str(uuid4())
    try:
        samples = [sample.to_contract(tenant_id, dataset_id) for sample in dataset.samples]
        version = build_dataset_version(
            tenant_id=tenant_id,
            source_id=dataset.source_id,
            name=dataset.name,
            version=dataset.version,
            intended_use=dataset.intended_use,
            samples=samples,
            dataset_id=dataset_id,
        )
        stored, created = await defensive_evaluation_repository.register_dataset(version, samples)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data={"dataset": stored.model_dump(mode="json"), "created": created})


@router.get("/defensive-data/datasets")
async def list_defensive_datasets(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_capability("audit:read")),
):
    datasets = await defensive_evaluation_repository.list_datasets(str(current_user.tenant_id), limit=limit)
    return success_response(data=[dataset.model_dump(mode="json") for dataset in datasets])


@router.post("/defensive-data/evaluation-policies", status_code=201)
async def upsert_defensive_evaluation_policy(
    policy: DefensiveEvaluationPolicyCreate,
    current_user: User = Depends(require_capability("response:approve")),
):
    try:
        stored = await defensive_evaluation_repository.upsert_policy(policy.to_contract(str(current_user.tenant_id)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=stored.model_dump(mode="json"))


@router.get("/defensive-data/evaluation-policies")
async def list_defensive_evaluation_policies(
    current_user: User = Depends(require_capability("audit:read")),
):
    policies = await defensive_evaluation_repository.list_policies(str(current_user.tenant_id))
    return success_response(data=[policy.model_dump(mode="json") for policy in policies])


@router.post("/defensive-data/evaluations", status_code=202)
async def evaluate_defensive_baseline(
    request: DefensiveEvaluationRunRequest,
    current_user: User = Depends(require_capability("response:approve")),
):
    """Run only the transparent offline baseline; result has no inference or containment authority."""
    try:
        evaluation = await defensive_evaluation_service.evaluate(
            tenant_id=str(current_user.tenant_id),
            policy_id=request.policy_id,
            dataset_id=request.dataset_id,
            classifier=RiskScoreThresholdClassifier(),
            split="test",
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=evaluation.model_dump(mode="json"))


@router.get("/defensive-data/evaluations")
async def list_defensive_evaluations(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_capability("audit:read")),
):
    evaluations = await defensive_evaluation_repository.list_evaluations(str(current_user.tenant_id), limit=limit)
    return success_response(data=[evaluation.model_dump(mode="json") for evaluation in evaluations])


@router.post("/defensive-data/advisory-assessments", status_code=202)
async def create_advisory_assessment(
    request: AdvisoryAssessmentRequest,
    current_user: User = Depends(require_capability("audit:read")),
):
    """Create an observation/investigation-only assessment for a stored same-tenant detection."""
    tenant_id = str(current_user.tenant_id)
    try:
        detection = await detection_repository.get_for_tenant(tenant_id, request.detection_id)
        candidate_ids = {detection.event_id}
        reported_ids = detection.evidence.get("evidence_ids")
        if isinstance(reported_ids, list):
            candidate_ids.update(str(value) for value in reported_ids[:16])
        records = await evidence_integration_service.list_for_tenant(tenant_id, limit=500)
        evidence = [
            record for record in records
            if record.evidence_id in candidate_ids or record.source_record_id in candidate_ids
        ][:16]
        assessment = await advisory_assessment_service.assess(
            detection=detection,
            evidence=evidence,
            evaluation_id=request.evaluation_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=assessment.model_dump(mode="json"))


@router.get("/defensive-data/advisory-assessments")
async def list_advisory_assessments(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(require_capability("audit:read")),
):
    assessments = await advisory_assessment_repository.list_for_tenant(str(current_user.tenant_id), limit=limit)
    return success_response(data=[assessment.model_dump(mode="json") for assessment in assessments])


@router.get("/autonomous-defense/policies")
async def list_autonomous_defense_policies(
    current_user: User = Depends(require_capability("audit:read")),
):
    policies = await autonomous_defense_repository.list_policies(str(current_user.tenant_id))
    return success_response(data=[policy.model_dump(mode="json") for policy in policies])


@router.post("/autonomous-defense/policies", status_code=201)
async def upsert_autonomous_defense_policy(
    policy: AutonomousDefensePolicyCreate,
    current_user: User = Depends(require_capability("response:approve")),
):
    try:
        stored = await autonomous_defense_repository.upsert_policy(policy.to_contract(str(current_user.tenant_id)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response(data=stored.model_dump(mode="json"))


@router.get("/autonomous-defense/decisions")
async def list_autonomous_defense_decisions(
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("audit:read")),
):
    decisions = await autonomous_defense_repository.list_decisions(str(current_user.tenant_id), limit=limit)
    return success_response(data=[decision.model_dump(mode="json") for decision in decisions])


async def _evaluate_durable_autonomous_detection(tenant_id: str, detection_id: str) -> dict[str, Any]:
    """Evaluate only a persisted, tenant-owned detection; it cannot execute an adapter."""
    try:
        detection = await detection_repository.get_for_tenant(tenant_id, detection_id)
        decisions = await autonomous_defense_service.evaluate_detection(detection)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Detection was not found for the authenticated tenant.") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "detection_id": detection_id,
        "decisions": [decision.model_dump(mode="json") for decision in decisions],
        "automatic_enforcement": False,
    }


@router.post("/autonomous-defense/detections/{detection_id}/evaluate", status_code=202)
async def evaluate_autonomous_defense_detection(
    detection_id: str,
    current_user: User = Depends(require_capability("response:request")),
):
    return success_response(
        data=await _evaluate_durable_autonomous_detection(str(current_user.tenant_id), detection_id)
    )


@router.post("/autonomous-defense/evaluate", status_code=202)
async def evaluate_autonomous_defense(
    request: AutonomousDefenseEvaluationRequest,
    current_user: User = Depends(require_capability("response:request")),
):
    return success_response(
        data=await _evaluate_durable_autonomous_detection(str(current_user.tenant_id), request.detection_id)
    )


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
