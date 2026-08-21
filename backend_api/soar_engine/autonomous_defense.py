"""Evidence-grounded autonomous defense decisions.

This module turns durable detections and tenant-owned read-only evidence into bounded policy
outcomes. It may record an observation/investigation decision or create a containment *proposal*.
It never executes a containment adapter: existing approval, signed-audit, verification, and rollback
controls remain the sole path to high-impact enforcement.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.evidence_vault.integration import EvidenceIntegrationService
from backend_api.shared.database import (
    AsyncSessionLocal,
    AutonomousDefenseDecisionRow,
    AutonomousDefensePolicyRow,
    engine,
)
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import (
    AutonomousDefenseDecision,
    AutonomousDefensePolicy,
    ContainmentRequest,
    DetectionRecord,
    IntegratedEvidenceRecord,
)


SessionFactory = Callable[[], AsyncSession]
SEVERITY_SCORE = {"informational": 0.20, "low": 0.40, "medium": 0.60, "high": 0.80, "critical": 0.95}
SEVERITY_ORDER = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _policy_contract(row: AutonomousDefensePolicyRow) -> AutonomousDefensePolicy:
    return AutonomousDefensePolicy(
        policy_id=row.policy_id,
        tenant_id=str(row.tenant_id),
        name=row.name,
        enabled=bool(row.enabled),
        trigger_rule_ids=list(row.trigger_rule_ids),
        minimum_severity=row.minimum_severity,
        decision_mode=row.decision_mode,
        minimum_confidence=float(row.minimum_confidence),
        minimum_evidence_count=int(row.minimum_evidence_count),
        required_evidence_kinds=list(row.required_evidence_kinds),
        cooldown_seconds=int(row.cooldown_seconds),
        max_decisions_per_hour=int(row.max_decisions_per_hour),
        containment_action=row.containment_action,
        target=row.target,
        asset_id=row.asset_id,
        parameters=dict(row.parameters),
        requires_approval=True,
        automatic_enforcement=False,
    )


def _decision_contract(row: AutonomousDefenseDecisionRow) -> AutonomousDefenseDecision:
    return AutonomousDefenseDecision(
        decision_id=row.decision_id,
        tenant_id=str(row.tenant_id),
        policy_id=row.policy_id,
        detection_id=row.detection_id,
        rule_id=row.rule_id,
        severity=row.severity,
        confidence=float(row.confidence),
        decision_mode=row.decision_mode,
        outcome=row.outcome,
        evidence_ids=list(row.evidence_ids),
        evidence_kinds=list(row.evidence_kinds),
        reasons=list(row.reasons),
        containment_request_id=row.containment_request_id,
        decided_at=row.decided_at,
        requires_human_approval=bool(row.requires_human_approval),
        automatic_enforcement=False,
    )


def decision_fingerprint(decision: AutonomousDefenseDecision) -> str:
    material = {
        "tenant_id": decision.tenant_id,
        "policy_id": decision.policy_id,
        "detection_id": decision.detection_id,
        "rule_id": decision.rule_id,
        "severity": decision.severity,
        "confidence": decision.confidence,
        "decision_mode": decision.decision_mode,
        "outcome": decision.outcome,
        "evidence_ids": decision.evidence_ids,
        "evidence_kinds": decision.evidence_kinds,
        "reasons": decision.reasons,
        "containment_request_id": decision.containment_request_id,
        "requires_human_approval": decision.requires_human_approval,
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


async def init_autonomous_defense_store() -> None:
    """Provision autonomous decision tables for isolated test environments only."""
    async with engine.begin() as connection:
        await connection.run_sync(AutonomousDefensePolicyRow.__table__.create, checkfirst=True)
        await connection.run_sync(AutonomousDefenseDecisionRow.__table__.create, checkfirst=True)


class AutonomousDefenseRepository:
    """Durable tenant-owned policy and decision persistence with immutable decisions."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def upsert_policy(self, policy: AutonomousDefensePolicy) -> AutonomousDefensePolicy:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(AutonomousDefensePolicyRow).where(
                    AutonomousDefensePolicyRow.tenant_id == UUID(policy.tenant_id),
                    AutonomousDefensePolicyRow.name == policy.name,
                )
            )
            now = datetime.now(timezone.utc)
            values = {
                "enabled": policy.enabled,
                "trigger_rule_ids": policy.trigger_rule_ids,
                "minimum_severity": policy.minimum_severity,
                "decision_mode": policy.decision_mode,
                "minimum_confidence": policy.minimum_confidence,
                "minimum_evidence_count": policy.minimum_evidence_count,
                "required_evidence_kinds": policy.required_evidence_kinds,
                "cooldown_seconds": policy.cooldown_seconds,
                "max_decisions_per_hour": policy.max_decisions_per_hour,
                "containment_action": policy.containment_action,
                "target": policy.target,
                "asset_id": policy.asset_id,
                "parameters": policy.parameters,
            }
            if row is None:
                row = AutonomousDefensePolicyRow(
                    policy_id=policy.policy_id,
                    tenant_id=UUID(policy.tenant_id),
                    name=policy.name,
                    created_at=now,
                    updated_at=now,
                    **values,
                )
                session.add(row)
            else:
                for key, value in values.items():
                    setattr(row, key, value)
                row.updated_at = now
            await session.commit()
            return _policy_contract(row)

    async def list_policies(self, tenant_id: str, enabled_only: bool = False) -> list[AutonomousDefensePolicy]:
        async with self._session_factory() as session:
            statement = select(AutonomousDefensePolicyRow).where(
                AutonomousDefensePolicyRow.tenant_id == UUID(tenant_id)
            )
            if enabled_only:
                statement = statement.where(AutonomousDefensePolicyRow.enabled.is_(True))
            rows = await session.scalars(statement.order_by(AutonomousDefensePolicyRow.name))
            return [_policy_contract(row) for row in rows]

    async def get_existing_for_detection(
        self, tenant_id: str, policy_id: str, detection_id: str
    ) -> AutonomousDefenseDecision | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(AutonomousDefenseDecisionRow)
                .where(
                    AutonomousDefenseDecisionRow.tenant_id == UUID(tenant_id),
                    AutonomousDefenseDecisionRow.policy_id == policy_id,
                    AutonomousDefenseDecisionRow.detection_id == detection_id,
                )
                .order_by(AutonomousDefenseDecisionRow.decided_at.desc())
            )
            return _decision_contract(row) if row is not None else None

    async def latest_for_policy(self, tenant_id: str, policy_id: str) -> AutonomousDefenseDecision | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(AutonomousDefenseDecisionRow)
                .where(
                    AutonomousDefenseDecisionRow.tenant_id == UUID(tenant_id),
                    AutonomousDefenseDecisionRow.policy_id == policy_id,
                )
                .order_by(AutonomousDefenseDecisionRow.decided_at.desc())
            )
            return _decision_contract(row) if row is not None else None

    async def decisions_in_window(self, tenant_id: str, policy_id: str, since: datetime) -> int:
        async with self._session_factory() as session:
            count = await session.scalar(
                select(func.count(AutonomousDefenseDecisionRow.id)).where(
                    AutonomousDefenseDecisionRow.tenant_id == UUID(tenant_id),
                    AutonomousDefenseDecisionRow.policy_id == policy_id,
                    AutonomousDefenseDecisionRow.decided_at >= since,
                )
            )
            return int(count or 0)

    async def persist_decision(self, decision: AutonomousDefenseDecision) -> tuple[AutonomousDefenseDecision, bool]:
        fingerprint = decision_fingerprint(decision)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(AutonomousDefenseDecisionRow).where(
                    AutonomousDefenseDecisionRow.tenant_id == UUID(decision.tenant_id),
                    AutonomousDefenseDecisionRow.policy_id == decision.policy_id,
                    AutonomousDefenseDecisionRow.detection_id == decision.detection_id,
                    AutonomousDefenseDecisionRow.decision_hash == fingerprint,
                )
            )
            if existing is not None:
                return _decision_contract(existing), False
            row = AutonomousDefenseDecisionRow(
                decision_id=decision.decision_id,
                tenant_id=UUID(decision.tenant_id),
                policy_id=decision.policy_id,
                detection_id=decision.detection_id,
                rule_id=decision.rule_id,
                severity=decision.severity,
                confidence=decision.confidence,
                decision_mode=decision.decision_mode,
                outcome=decision.outcome,
                evidence_ids=decision.evidence_ids,
                evidence_kinds=decision.evidence_kinds,
                reasons=decision.reasons,
                containment_request_id=decision.containment_request_id,
                requires_human_approval=True,
                decision_hash=fingerprint,
                decided_at=decision.decided_at,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await session.scalar(
                    select(AutonomousDefenseDecisionRow).where(
                        AutonomousDefenseDecisionRow.tenant_id == UUID(decision.tenant_id),
                        AutonomousDefenseDecisionRow.policy_id == decision.policy_id,
                        AutonomousDefenseDecisionRow.detection_id == decision.detection_id,
                        AutonomousDefenseDecisionRow.decision_hash == fingerprint,
                    )
                )
                if existing is None:
                    raise
                return _decision_contract(existing), False
            return _decision_contract(row), True

    async def list_decisions(self, tenant_id: str, limit: int = 100) -> list[AutonomousDefenseDecision]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(AutonomousDefenseDecisionRow)
                .where(AutonomousDefenseDecisionRow.tenant_id == UUID(tenant_id))
                .order_by(AutonomousDefenseDecisionRow.decided_at.desc(), AutonomousDefenseDecisionRow.decision_id)
                .limit(safe_limit)
            )
            return [_decision_contract(row) for row in rows]


class DeterministicEvidenceConfidenceModel:
    """Safe baseline scorer used when no separately evaluated model provider is configured.

    The score is reproducible and deliberately limited to severity plus distinct, source-bound evidence.
    A future model provider may supply a bounded assessment only through the same policy gate.
    """

    def score(self, detection: DetectionRecord, evidence: list[IntegratedEvidenceRecord]) -> tuple[float, list[str]]:
        severity_score = SEVERITY_SCORE[detection.severity]
        kinds = sorted({record.source_kind for record in evidence})
        evidence_bonus = min(0.15, max(0, len(evidence) - 1) * 0.05)
        diversity_bonus = min(0.10, max(0, len(kinds) - 1) * 0.05)
        confidence = min(1.0, severity_score + evidence_bonus + diversity_bonus)
        reasons = [
            f"severity={detection.severity} base_score={severity_score:.2f}",
            f"linked_evidence_count={len(evidence)}",
            f"linked_evidence_kinds={','.join(kinds) if kinds else 'none'}",
        ]
        return confidence, reasons


class AutonomousDefenseDecisionService:
    """Evaluate detections against tenant policy and produce bounded autonomous decisions."""

    def __init__(
        self,
        repository: AutonomousDefenseRepository,
        evidence: EvidenceIntegrationService,
        containment: GovernedContainmentService,
        confidence_model: DeterministicEvidenceConfidenceModel | None = None,
    ) -> None:
        self._repository = repository
        self._evidence = evidence
        self._containment = containment
        self._confidence_model = confidence_model or DeterministicEvidenceConfidenceModel()

    async def evaluate_detection(self, detection: DetectionRecord) -> list[AutonomousDefenseDecision]:
        policies = await self._repository.list_policies(detection.tenant_id, enabled_only=True)
        if not policies:
            return []
        linked_evidence = await self._linked_evidence(detection)
        confidence, base_reasons = self._confidence_model.score(detection, linked_evidence)
        decisions: list[AutonomousDefenseDecision] = []
        for policy in policies:
            if policy.trigger_rule_ids and detection.rule_id not in policy.trigger_rule_ids:
                continue
            if SEVERITY_ORDER[detection.severity] < SEVERITY_ORDER[policy.minimum_severity]:
                continue
            existing = await self._repository.get_existing_for_detection(
                detection.tenant_id, policy.policy_id, detection.detection_id
            )
            if existing is not None:
                decisions.append(existing)
                continue
            decision = await self._evaluate_policy(
                policy=policy,
                detection=detection,
                evidence=linked_evidence,
                confidence=confidence,
                base_reasons=base_reasons,
            )
            stored, _ = await self._repository.persist_decision(decision)
            decisions.append(stored)
        return decisions

    async def _linked_evidence(self, detection: DetectionRecord) -> list[IntegratedEvidenceRecord]:
        candidate_ids = {detection.event_id}
        evidence_ids = detection.evidence.get("evidence_ids")
        if isinstance(evidence_ids, list):
            candidate_ids.update(str(value) for value in evidence_ids[:16])
        records = await self._evidence.list_for_tenant(detection.tenant_id, limit=500)
        return [
            record
            for record in records
            if record.evidence_id in candidate_ids or record.source_record_id in candidate_ids
        ][:16]

    async def _evaluate_policy(
        self,
        *,
        policy: AutonomousDefensePolicy,
        detection: DetectionRecord,
        evidence: list[IntegratedEvidenceRecord],
        confidence: float,
        base_reasons: list[str],
    ) -> AutonomousDefenseDecision:
        evidence_ids = [record.evidence_id for record in evidence]
        evidence_kinds = sorted({record.source_kind for record in evidence})
        reasons = list(base_reasons)
        now = datetime.now(timezone.utc)

        latest = await self._repository.latest_for_policy(detection.tenant_id, policy.policy_id)
        if latest is not None and now - latest.decided_at < timedelta(seconds=policy.cooldown_seconds):
            return self._decision(
                policy, detection, confidence, "rate_limited", evidence_ids, evidence_kinds,
                reasons + [f"cooldown_seconds={policy.cooldown_seconds} not elapsed"],
            )
        hourly_count = await self._repository.decisions_in_window(
            detection.tenant_id, policy.policy_id, now - timedelta(hours=1)
        )
        if hourly_count >= policy.max_decisions_per_hour:
            return self._decision(
                policy, detection, confidence, "rate_limited", evidence_ids, evidence_kinds,
                reasons + [f"max_decisions_per_hour={policy.max_decisions_per_hour} reached"],
            )
        if len(evidence) < policy.minimum_evidence_count:
            return self._decision(
                policy, detection, confidence, "refused", evidence_ids, evidence_kinds,
                reasons + [f"minimum_evidence_count={policy.minimum_evidence_count} not met"],
            )
        missing_kinds = sorted(set(policy.required_evidence_kinds) - set(evidence_kinds))
        if missing_kinds:
            return self._decision(
                policy, detection, confidence, "refused", evidence_ids, evidence_kinds,
                reasons + [f"required_evidence_kinds missing={','.join(missing_kinds)}"],
            )
        if confidence < policy.minimum_confidence:
            return self._decision(
                policy, detection, confidence, "refused", evidence_ids, evidence_kinds,
                reasons + [f"minimum_confidence={policy.minimum_confidence:.2f} not met"],
            )
        if policy.decision_mode != "propose_containment":
            return self._decision(
                policy, detection, confidence, "decision_recorded", evidence_ids, evidence_kinds,
                reasons + ["policy authority is limited to an advisory investigation decision"],
            )

        # Preallocate identifiers so both immutable records can link to each other without any
        # subsequent decision update. Request persistence still determines the canonical request ID
        # in an idempotent race.
        decision_id = str(uuid4())
        self._containment.require_signed_audit_configuration()
        idempotency_key = sha256(
            f"autonomous-defense:{policy.policy_id}:detection:{detection.detection_id}".encode("utf-8")
        ).hexdigest()
        request, _ = await self._containment.request(
            ContainmentRequest(
                request_id=str(uuid4()),
                tenant_id=detection.tenant_id,
                action=policy.containment_action,
                target=policy.target,
                asset_id=policy.asset_id,
                requested_by=f"autonomous-defense-policy:{policy.policy_id}",
                idempotency_key=idempotency_key,
                parameters={
                    **policy.parameters,
                    "autonomous_decision_id": decision_id,
                    "source_detection_id": detection.detection_id,
                    "source_rule_id": detection.rule_id,
                    "evidence_ids": evidence_ids,
                    "decision_confidence": confidence,
                },
                requires_approval=True,
                automatic_enforcement=False,
            )
        )
        return self._decision(
            policy,
            detection,
            confidence,
            "containment_proposed",
            evidence_ids,
            evidence_kinds,
            reasons + ["containment proposal requires separate human approval before execution"],
            decision_id=decision_id,
            containment_request_id=request.request_id,
        )

    @staticmethod
    def _decision(
        policy: AutonomousDefensePolicy,
        detection: DetectionRecord,
        confidence: float,
        outcome: str,
        evidence_ids: list[str],
        evidence_kinds: list[str],
        reasons: list[str],
        decision_id: str | None = None,
        containment_request_id: str | None = None,
    ) -> AutonomousDefenseDecision:
        return AutonomousDefenseDecision(
            decision_id=decision_id or str(uuid4()),
            tenant_id=detection.tenant_id,
            policy_id=policy.policy_id,
            detection_id=detection.detection_id,
            rule_id=detection.rule_id,
            severity=detection.severity,
            confidence=confidence,
            decision_mode=policy.decision_mode,
            outcome=outcome,
            evidence_ids=evidence_ids,
            evidence_kinds=evidence_kinds,
            reasons=reasons,
            containment_request_id=containment_request_id,
            requires_human_approval=True,
            automatic_enforcement=False,
        )


class AutonomousDefenseObserver:
    """Best-effort post-persistence evaluator that cannot interrupt governed detection storage."""

    def __init__(self, decisions: AutonomousDefenseDecisionService) -> None:
        self._decisions = decisions

    async def observe(self, detection: DetectionRecord) -> list[AutonomousDefenseDecision]:
        try:
            return await self._decisions.evaluate_detection(detection)
        except PermissionError:
            # A proposal-mode policy cannot create a high-impact request without the signed-audit
            # configuration mandated by the governed containment lifecycle. The durable detection
            # remains available to analysts; no adapter execution is attempted.
            import logging

            logging.getLogger(__name__).error(
                "Autonomous-defense containment proposal refused because audit configuration is unavailable.",
                extra={"tenant_id": detection.tenant_id, "detection_id": detection.detection_id},
            )
            return []
