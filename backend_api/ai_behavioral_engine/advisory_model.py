"""Evidence-bound advisory model assessment.

Model output in this module is deliberately limited to observation or investigation guidance. Before
an assessment can be created, the exact provider model/version must have an accepted evaluation on
a tenant-owned sanitized corpus. The service never constructs containment requests, calls adapters,
approves actions, or exposes response fields in its output schema.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from typing import Literal, Protocol
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.ai_behavioral_engine.defensive_evaluation import DefensiveEvaluationRepository
from backend_api.shared.database import AdvisoryModelAssessmentRow, AsyncSessionLocal, engine
from phantomnet_core.contracts import (
    AdvisoryModelAssessment,
    DefensiveModelEvaluation,
    DetectionRecord,
    IntegratedEvidenceRecord,
)


SessionFactory = Callable[[], AsyncSession]


@dataclass(frozen=True)
class ProviderAssessment:
    """Validated, response-free provider result before immutable evidence linkage is applied."""

    classification: Literal["likely_benign", "suspicious", "insufficient_evidence"]
    confidence: float
    reasons: list[str]
    recommended_mode: Literal["observe", "investigate"]


class AdvisoryAssessmentProvider(Protocol):
    """An injected advisory provider; implementations have no response or adapter interface."""

    model_id: str
    model_version: str

    async def assess(
        self,
        detection: DetectionRecord,
        evidence: Sequence[IntegratedEvidenceRecord],
    ) -> ProviderAssessment:
        """Return only a structured observation/investigation recommendation."""


def assessment_fingerprint(assessment: AdvisoryModelAssessment) -> str:
    material = {
        "tenant_id": assessment.tenant_id,
        "detection_id": assessment.detection_id,
        "model_id": assessment.model_id,
        "model_version": assessment.model_version,
        "evaluation_id": assessment.evaluation_id,
        "classification": assessment.classification,
        "confidence": assessment.confidence,
        "evidence_ids": assessment.evidence_ids,
        "reasons": assessment.reasons,
        "recommended_mode": assessment.recommended_mode,
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _assessment_contract(row: AdvisoryModelAssessmentRow) -> AdvisoryModelAssessment:
    return AdvisoryModelAssessment(
        assessment_id=row.assessment_id,
        tenant_id=str(row.tenant_id),
        detection_id=row.detection_id,
        model_id=row.model_id,
        model_version=row.model_version,
        evaluation_id=row.evaluation_id,
        classification=row.classification,
        confidence=float(row.confidence),
        evidence_ids=list(row.evidence_ids),
        reasons=list(row.reasons),
        recommended_mode=row.recommended_mode,
        assessed_at=row.assessed_at,
        advisory_only=bool(row.advisory_only),
        requires_human_approval=bool(row.requires_human_approval),
        automatic_enforcement=bool(row.automatic_enforcement),
    )


async def init_advisory_model_store() -> None:
    """Provision immutable advisory assessment storage for isolated tests only."""
    async with engine.begin() as connection:
        await connection.run_sync(AdvisoryModelAssessmentRow.__table__.create, checkfirst=True)


class AdvisoryModelAssessmentRepository:
    """Immutable tenant-scoped advisory assessment persistence."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def persist(self, assessment: AdvisoryModelAssessment) -> tuple[AdvisoryModelAssessment, bool]:
        fingerprint = assessment_fingerprint(assessment)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(AdvisoryModelAssessmentRow).where(
                    AdvisoryModelAssessmentRow.tenant_id == UUID(assessment.tenant_id),
                    AdvisoryModelAssessmentRow.detection_id == assessment.detection_id,
                    AdvisoryModelAssessmentRow.model_id == assessment.model_id,
                    AdvisoryModelAssessmentRow.model_version == assessment.model_version,
                    AdvisoryModelAssessmentRow.assessment_fingerprint == fingerprint,
                )
            )
            if existing is not None:
                return _assessment_contract(existing), False
            row = AdvisoryModelAssessmentRow(
                assessment_id=assessment.assessment_id,
                tenant_id=UUID(assessment.tenant_id),
                detection_id=assessment.detection_id,
                model_id=assessment.model_id,
                model_version=assessment.model_version,
                evaluation_id=assessment.evaluation_id,
                classification=assessment.classification,
                confidence=assessment.confidence,
                evidence_ids=assessment.evidence_ids,
                reasons=assessment.reasons,
                recommended_mode=assessment.recommended_mode,
                assessment_fingerprint=fingerprint,
                assessed_at=assessment.assessed_at,
                advisory_only=True,
                requires_human_approval=True,
                automatic_enforcement=False,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await session.scalar(
                    select(AdvisoryModelAssessmentRow).where(
                        AdvisoryModelAssessmentRow.tenant_id == UUID(assessment.tenant_id),
                        AdvisoryModelAssessmentRow.detection_id == assessment.detection_id,
                        AdvisoryModelAssessmentRow.model_id == assessment.model_id,
                        AdvisoryModelAssessmentRow.model_version == assessment.model_version,
                        AdvisoryModelAssessmentRow.assessment_fingerprint == fingerprint,
                    )
                )
                if existing is None:
                    raise
                return _assessment_contract(existing), False
            return _assessment_contract(row), True

    async def list_for_tenant(self, tenant_id: str, limit: int = 100) -> list[AdvisoryModelAssessment]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(AdvisoryModelAssessmentRow)
                .where(AdvisoryModelAssessmentRow.tenant_id == UUID(tenant_id))
                .order_by(AdvisoryModelAssessmentRow.assessed_at.desc(), AdvisoryModelAssessmentRow.assessment_id)
                .limit(safe_limit)
            )
            return [_assessment_contract(row) for row in rows]


class DeterministicAdvisoryProvider:
    """Transparent risk-score provider that exactly matches the offline evaluation baseline."""

    model_id = "deterministic-risk-score-baseline"
    model_version = "1.0.0"

    def __init__(self, threshold: float = 0.50) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("risk score threshold must be within [0.0, 1.0].")
        self._threshold = threshold

    async def assess(
        self,
        detection: DetectionRecord,
        evidence: Sequence[IntegratedEvidenceRecord],
    ) -> ProviderAssessment:
        risk_score = detection.evidence.get("risk_score")
        if not evidence or isinstance(risk_score, bool) or not isinstance(risk_score, (int, float)):
            return ProviderAssessment(
                classification="insufficient_evidence",
                confidence=0.0,
                reasons=["A linked tenant-scoped evidence record and numeric detection risk_score are required."],
                recommended_mode="observe",
            )
        score = float(risk_score)
        if not 0.0 <= score <= 1.0:
            raise ValueError("Persisted detection risk_score must be within [0.0, 1.0].")
        if score >= self._threshold:
            return ProviderAssessment(
                classification="suspicious",
                confidence=score,
                reasons=[
                    f"Persisted detection risk_score={score:.4f} is at or above threshold={self._threshold:.4f}.",
                    f"Linked integrated evidence count is {len(evidence)}.",
                ],
                recommended_mode="investigate",
            )
        return ProviderAssessment(
            classification="likely_benign",
            confidence=1.0 - score,
            reasons=[
                f"Persisted detection risk_score={score:.4f} is below threshold={self._threshold:.4f}.",
                f"Linked integrated evidence count is {len(evidence)}.",
            ],
            recommended_mode="observe",
        )


class OpenAICompatibleAdvisoryProvider:
    """Optional structured provider, disabled unless explicitly constructed by an operator.

    The provider sends only detection metadata and evidence provenance identifiers, not raw evidence
    payloads. It returns a fixed JSON schema with no action, target, command, tool, or containment
    field. Tests inject an HTTP transport; production callers must opt in through configuration.
    """

    _response_schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "phantomnet_advisory_assessment",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "classification": {
                        "type": "string",
                        "enum": ["likely_benign", "suspicious", "insufficient_evidence"],
                    },
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "reasons": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 3, "maxLength": 500},
                        "minItems": 1,
                        "maxItems": 12,
                    },
                    "recommended_mode": {"type": "string", "enum": ["observe", "investigate"]},
                },
                "required": ["classification", "confidence", "reasons", "recommended_mode"],
                "additionalProperties": False,
            },
        },
    }

    def __init__(
        self,
        *,
        model_id: str,
        model_version: str,
        api_key: str,
        base_url: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not model_id or not model_version or not api_key or not base_url:
            raise ValueError("An advisory provider requires explicit model, version, API key, and base URL configuration.")
        self.model_id = model_id
        self.model_version = model_version
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client

    @classmethod
    def from_environment(cls) -> "OpenAICompatibleAdvisoryProvider | None":
        if os.getenv("PHANTOMNET_ADVISORY_MODEL_ENABLED", "false").lower() != "true":
            return None
        model_id = os.getenv("PHANTOMNET_ADVISORY_MODEL_ID", "gpt-5-mini")
        model_version = os.getenv("PHANTOMNET_ADVISORY_MODEL_VERSION", "operator-managed")
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE")
        if not api_key or not base_url:
            raise RuntimeError("Advisory model was enabled but OPENAI_API_KEY or OPENAI_API_BASE is unavailable.")
        return cls(
            model_id=model_id,
            model_version=model_version,
            api_key=api_key,
            base_url=base_url,
        )

    async def assess(
        self,
        detection: DetectionRecord,
        evidence: Sequence[IntegratedEvidenceRecord],
    ) -> ProviderAssessment:
        context = {
            "detection_id": detection.detection_id,
            "rule_id": detection.rule_id,
            "severity": detection.severity,
            "title": detection.title,
            "evidence": [
                {
                    "evidence_id": record.evidence_id,
                    "source_kind": record.source_kind,
                    "source_name": record.source_name,
                    "source_record_id": record.source_record_id,
                    "tags": record.tags,
                }
                for record in evidence
            ],
        }
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are PhantomNet's advisory security triage component. Return JSON only. "
                        "Use only provided evidence. You may recommend observe or investigate, never a response action. "
                        "If evidence is insufficient, classify insufficient_evidence and recommend observe."
                    ),
                },
                {"role": "user", "content": json.dumps(context, sort_keys=True)},
            ],
            "response_format": self._response_schema,
            "max_completion_tokens": 800,
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
        if self._client is not None:
            response = await self._client.post(
                f"{self._base_url}/chat/completions", headers=headers, json=payload, timeout=30.0
            )
            response.raise_for_status()
            body = response.json()
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions", headers=headers, json=payload, timeout=30.0
                )
                response.raise_for_status()
                body = response.json()
        try:
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            result = ProviderAssessment(
                classification=parsed["classification"],
                confidence=float(parsed["confidence"]),
                reasons=list(parsed["reasons"]),
                recommended_mode=parsed["recommended_mode"],
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Advisory provider returned an invalid structured assessment.") from exc
        if result.classification == "insufficient_evidence" and result.recommended_mode != "observe":
            raise ValueError("Advisory provider attempted an unsafe recommendation for insufficient evidence.")
        return result


class AdvisoryModelAssessmentService:
    """Gate advisory provider output on accepted evaluation evidence and immutable record storage."""

    def __init__(
        self,
        evaluations: DefensiveEvaluationRepository,
        assessments: AdvisoryModelAssessmentRepository,
        provider: AdvisoryAssessmentProvider,
    ) -> None:
        self._evaluations = evaluations
        self._assessments = assessments
        self._provider = provider

    async def assess(
        self,
        *,
        detection: DetectionRecord,
        evidence: Sequence[IntegratedEvidenceRecord],
        evaluation_id: str,
    ) -> AdvisoryModelAssessment:
        if any(record.tenant_id != detection.tenant_id for record in evidence):
            raise PermissionError("Advisory assessment evidence must belong to the detection tenant.")
        evaluation = await self._accepted_evaluation(detection.tenant_id, evaluation_id)
        if evaluation.model_id != self._provider.model_id or evaluation.model_version != self._provider.model_version:
            raise PermissionError("The provider model and version do not match the accepted defensive evaluation.")
        linked_evidence = list(evidence[:16])
        if not linked_evidence:
            provider_result = ProviderAssessment(
                classification="insufficient_evidence",
                confidence=0.0,
                reasons=["No linked tenant-scoped integrated evidence was supplied for advisory assessment."],
                recommended_mode="observe",
            )
        else:
            provider_result = await self._provider.assess(detection, linked_evidence)
        assessment = AdvisoryModelAssessment(
            tenant_id=detection.tenant_id,
            detection_id=detection.detection_id,
            model_id=self._provider.model_id,
            model_version=self._provider.model_version,
            evaluation_id=evaluation.evaluation_id,
            classification=provider_result.classification,
            confidence=provider_result.confidence,
            evidence_ids=[record.evidence_id for record in linked_evidence],
            reasons=provider_result.reasons,
            recommended_mode=provider_result.recommended_mode,
            advisory_only=True,
            requires_human_approval=True,
            automatic_enforcement=False,
        )
        return (await self._assessments.persist(assessment))[0]

    async def _accepted_evaluation(self, tenant_id: str, evaluation_id: str) -> DefensiveModelEvaluation:
        evaluation = await self._evaluations.get_evaluation(tenant_id, evaluation_id)
        if evaluation.status != "accepted":
            raise PermissionError("Only an accepted defensive model evaluation may gate advisory inference.")
        return evaluation
