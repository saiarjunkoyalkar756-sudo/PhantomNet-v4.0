"""Governed defensive-data registration and advisory model evaluation.

The service stores only minimized, sanitized, tenant-scoped labelled features. It evaluates an
advisory classifier against a versioned corpus and persists immutable metrics. No function in this
module can ingest raw telemetry, dispatch a containment adapter, approve a response, or alter a
model's response authority.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AsyncSessionLocal,
    DefensiveDatasetSampleRow,
    DefensiveDatasetSourceRow,
    DefensiveDatasetVersionRow,
    DefensiveEvaluationPolicyRow,
    DefensiveModelEvaluationRow,
    engine,
)
from phantomnet_core.contracts import (
    DefensiveDatasetSample,
    DefensiveDatasetSource,
    DefensiveDatasetVersion,
    DefensiveEvaluationPolicy,
    DefensiveModelEvaluation,
)


SessionFactory = Callable[[], AsyncSession]


class DefensiveClassifier(Protocol):
    """A mockable advisory-only binary classifier used only for offline evaluation."""

    model_id: str
    model_version: str

    def predicts_attack(self, sample: DefensiveDatasetSample) -> bool:
        """Return an offline attack classification; this method has no external side effect."""


def _source_contract(row: DefensiveDatasetSourceRow) -> DefensiveDatasetSource:
    return DefensiveDatasetSource(
        source_id=row.source_id,
        tenant_id=str(row.tenant_id),
        name=row.name,
        source_type=row.source_type,
        source_uri=row.source_uri,
        source_fingerprint=row.source_fingerprint,
        license_reference=row.license_reference,
        operator_approved=bool(row.operator_approved),
        license_reviewed=bool(row.license_reviewed),
        contains_raw_telemetry=False,
        sanitization_attested=bool(row.sanitization_attested),
        approved_by=row.approved_by,
        approved_at=row.approved_at,
        automatic_enforcement=False,
    )


def _dataset_contract(row: DefensiveDatasetVersionRow) -> DefensiveDatasetVersion:
    return DefensiveDatasetVersion(
        dataset_id=row.dataset_id,
        tenant_id=str(row.tenant_id),
        source_id=row.source_id,
        name=row.name,
        version=row.version,
        dataset_fingerprint=row.dataset_fingerprint,
        intended_use=row.intended_use,
        sample_count=int(row.sample_count),
        attack_sample_count=int(row.attack_sample_count),
        benign_sample_count=int(row.benign_sample_count),
        training_split_count=int(row.training_split_count),
        validation_split_count=int(row.validation_split_count),
        test_split_count=int(row.test_split_count),
        contains_raw_telemetry=False,
        sanitization_attested=bool(row.sanitization_attested),
        created_at=row.created_at,
        automatic_enforcement=False,
    )


def _sample_contract(row: DefensiveDatasetSampleRow) -> DefensiveDatasetSample:
    return DefensiveDatasetSample(
        sample_id=row.sample_id,
        tenant_id=str(row.tenant_id),
        dataset_id=row.dataset_id,
        split=row.split,
        label=row.label,
        attack_family=row.attack_family,
        mitre_techniques=list(row.mitre_techniques),
        feature_payload=dict(row.feature_payload),
        source_record_fingerprint=row.source_record_fingerprint,
        sanitized=True,
        automatic_enforcement=False,
    )


def _policy_contract(row: DefensiveEvaluationPolicyRow) -> DefensiveEvaluationPolicy:
    return DefensiveEvaluationPolicy(
        policy_id=row.policy_id,
        tenant_id=str(row.tenant_id),
        name=row.name,
        enabled=bool(row.enabled),
        minimum_precision=float(row.minimum_precision),
        minimum_recall=float(row.minimum_recall),
        maximum_false_positive_rate=float(row.maximum_false_positive_rate),
        minimum_attack_samples=int(row.minimum_attack_samples),
        minimum_benign_samples=int(row.minimum_benign_samples),
        require_test_split=bool(row.require_test_split),
        advisory_only=True,
        automatic_enforcement=False,
    )


def _evaluation_contract(row: DefensiveModelEvaluationRow) -> DefensiveModelEvaluation:
    return DefensiveModelEvaluation(
        evaluation_id=row.evaluation_id,
        tenant_id=str(row.tenant_id),
        policy_id=row.policy_id,
        dataset_id=row.dataset_id,
        dataset_version=row.dataset_version,
        dataset_fingerprint=row.dataset_fingerprint,
        model_id=row.model_id,
        model_version=row.model_version,
        evaluated_split=row.evaluated_split,
        true_positive=int(row.true_positive),
        false_positive=int(row.false_positive),
        true_negative=int(row.true_negative),
        false_negative=int(row.false_negative),
        precision=float(row.precision),
        recall=float(row.recall),
        false_positive_rate=float(row.false_positive_rate),
        status=row.status,
        rejection_reasons=list(row.rejection_reasons),
        evaluated_at=row.evaluated_at,
        advisory_only=bool(row.advisory_only),
        requires_human_approval=bool(row.requires_human_approval),
        automatic_enforcement=bool(row.automatic_enforcement),
    )


def defensive_dataset_fingerprint(samples: Sequence[DefensiveDatasetSample]) -> str:
    """Calculate a stable corpus identity from label and sanitized feature evidence only."""
    material = [
        {
            "split": sample.split,
            "label": sample.label,
            "attack_family": sample.attack_family,
            "mitre_techniques": sample.mitre_techniques,
            "feature_payload": sample.feature_payload,
            "source_record_fingerprint": sample.source_record_fingerprint,
        }
        for sample in samples
    ]
    canonical = json.dumps(
        sorted(material, key=lambda item: (item["split"], item["source_record_fingerprint"])),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def defensive_evaluation_fingerprint(evaluation: DefensiveModelEvaluation) -> str:
    material = {
        "tenant_id": evaluation.tenant_id,
        "policy_id": evaluation.policy_id,
        "dataset_id": evaluation.dataset_id,
        "dataset_version": evaluation.dataset_version,
        "dataset_fingerprint": evaluation.dataset_fingerprint,
        "model_id": evaluation.model_id,
        "model_version": evaluation.model_version,
        "evaluated_split": evaluation.evaluated_split,
        "true_positive": evaluation.true_positive,
        "false_positive": evaluation.false_positive,
        "true_negative": evaluation.true_negative,
        "false_negative": evaluation.false_negative,
        "precision": evaluation.precision,
        "recall": evaluation.recall,
        "false_positive_rate": evaluation.false_positive_rate,
        "status": evaluation.status,
        "rejection_reasons": evaluation.rejection_reasons,
    }
    return sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_dataset_version(
    *,
    tenant_id: str,
    source_id: str,
    name: str,
    version: str,
    intended_use: str,
    samples: Sequence[DefensiveDatasetSample],
    dataset_id: str | None = None,
) -> DefensiveDatasetVersion:
    """Derive count metadata and a reproducible fingerprint from a sanitized labelled sample set."""
    if not samples:
        raise ValueError("A defensive dataset version requires at least one labelled sanitized sample.")
    generated_dataset_id = dataset_id or str(uuid4())
    if any(sample.tenant_id != tenant_id for sample in samples):
        raise ValueError("All defensive samples must belong to the dataset tenant.")
    if any(sample.dataset_id != generated_dataset_id for sample in samples):
        raise ValueError("All defensive samples must reference the dataset_id being registered.")
    counts = {split: sum(1 for sample in samples if sample.split == split) for split in ("train", "validation", "test")}
    attack_count = sum(1 for sample in samples if sample.label == "attack")
    return DefensiveDatasetVersion(
        dataset_id=generated_dataset_id,
        tenant_id=tenant_id,
        source_id=source_id,
        name=name,
        version=version,
        dataset_fingerprint=defensive_dataset_fingerprint(samples),
        intended_use=intended_use,
        sample_count=len(samples),
        attack_sample_count=attack_count,
        benign_sample_count=len(samples) - attack_count,
        training_split_count=counts["train"],
        validation_split_count=counts["validation"],
        test_split_count=counts["test"],
        contains_raw_telemetry=False,
        sanitization_attested=True,
        automatic_enforcement=False,
    )


async def init_defensive_evaluation_store() -> None:
    """Provision only evaluation storage for isolated test environments when migrations are absent."""
    async with engine.begin() as connection:
        for table in (
            DefensiveDatasetSourceRow.__table__,
            DefensiveDatasetVersionRow.__table__,
            DefensiveDatasetSampleRow.__table__,
            DefensiveEvaluationPolicyRow.__table__,
            DefensiveModelEvaluationRow.__table__,
        ):
            await connection.run_sync(table.create, checkfirst=True)


class DefensiveEvaluationRepository:
    """Tenant-bound persistence for sanitized corpus metadata and immutable evaluation evidence."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def register_source(self, source: DefensiveDatasetSource) -> tuple[DefensiveDatasetSource, bool]:
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(DefensiveDatasetSourceRow).where(
                    DefensiveDatasetSourceRow.tenant_id == UUID(source.tenant_id),
                    DefensiveDatasetSourceRow.name == source.name,
                    DefensiveDatasetSourceRow.source_fingerprint == source.source_fingerprint,
                )
            )
            if existing is not None:
                return _source_contract(existing), False
            row = DefensiveDatasetSourceRow(
                source_id=source.source_id,
                tenant_id=UUID(source.tenant_id),
                name=source.name,
                source_type=source.source_type,
                source_uri=source.source_uri,
                source_fingerprint=source.source_fingerprint,
                license_reference=source.license_reference,
                operator_approved=source.operator_approved,
                license_reviewed=source.license_reviewed,
                sanitization_attested=True,
                approved_by=source.approved_by,
                approved_at=source.approved_at,
                created_at=datetime.now(timezone.utc),
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await session.scalar(
                    select(DefensiveDatasetSourceRow).where(
                        DefensiveDatasetSourceRow.tenant_id == UUID(source.tenant_id),
                        DefensiveDatasetSourceRow.name == source.name,
                        DefensiveDatasetSourceRow.source_fingerprint == source.source_fingerprint,
                    )
                )
                if existing is None:
                    raise
                return _source_contract(existing), False
            return _source_contract(row), True

    async def register_dataset(
        self, dataset: DefensiveDatasetVersion, samples: Sequence[DefensiveDatasetSample]
    ) -> tuple[DefensiveDatasetVersion, bool]:
        if defensive_dataset_fingerprint(samples) != dataset.dataset_fingerprint:
            raise ValueError("Dataset fingerprint does not match the supplied sanitized sample corpus.")
        if len(samples) != dataset.sample_count:
            raise ValueError("Dataset sample_count does not match supplied samples.")
        if any(sample.tenant_id != dataset.tenant_id or sample.dataset_id != dataset.dataset_id for sample in samples):
            raise ValueError("Dataset samples must match the dataset tenant and dataset_id.")
        async with self._session_factory() as session:
            source = await session.scalar(
                select(DefensiveDatasetSourceRow).where(
                    DefensiveDatasetSourceRow.tenant_id == UUID(dataset.tenant_id),
                    DefensiveDatasetSourceRow.source_id == dataset.source_id,
                )
            )
            if source is None:
                raise LookupError("Approved defensive dataset source was not found for the tenant.")
            existing = await session.scalar(
                select(DefensiveDatasetVersionRow).where(
                    DefensiveDatasetVersionRow.tenant_id == UUID(dataset.tenant_id),
                    DefensiveDatasetVersionRow.name == dataset.name,
                    DefensiveDatasetVersionRow.version == dataset.version,
                )
            )
            if existing is not None:
                if existing.dataset_fingerprint != dataset.dataset_fingerprint:
                    raise ValueError("Dataset name and version already exist with a different corpus fingerprint.")
                return _dataset_contract(existing), False
            row = DefensiveDatasetVersionRow(
                dataset_id=dataset.dataset_id,
                tenant_id=UUID(dataset.tenant_id),
                source_id=dataset.source_id,
                name=dataset.name,
                version=dataset.version,
                dataset_fingerprint=dataset.dataset_fingerprint,
                intended_use=dataset.intended_use,
                sample_count=dataset.sample_count,
                attack_sample_count=dataset.attack_sample_count,
                benign_sample_count=dataset.benign_sample_count,
                training_split_count=dataset.training_split_count,
                validation_split_count=dataset.validation_split_count,
                test_split_count=dataset.test_split_count,
                sanitization_attested=True,
                created_at=dataset.created_at,
            )
            session.add(row)
            for sample in samples:
                session.add(
                    DefensiveDatasetSampleRow(
                        sample_id=sample.sample_id,
                        tenant_id=UUID(sample.tenant_id),
                        dataset_id=sample.dataset_id,
                        split=sample.split,
                        label=sample.label,
                        attack_family=sample.attack_family,
                        mitre_techniques=sample.mitre_techniques,
                        feature_payload=sample.feature_payload,
                        source_record_fingerprint=sample.source_record_fingerprint,
                        created_at=datetime.now(timezone.utc),
                    )
                )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                existing = await session.scalar(
                    select(DefensiveDatasetVersionRow).where(
                        DefensiveDatasetVersionRow.tenant_id == UUID(dataset.tenant_id),
                        DefensiveDatasetVersionRow.name == dataset.name,
                        DefensiveDatasetVersionRow.version == dataset.version,
                    )
                )
                if existing is None or existing.dataset_fingerprint != dataset.dataset_fingerprint:
                    raise
                return _dataset_contract(existing), False
            return _dataset_contract(row), True

    async def get_dataset(self, tenant_id: str, dataset_id: str) -> DefensiveDatasetVersion:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(DefensiveDatasetVersionRow).where(
                    DefensiveDatasetVersionRow.tenant_id == UUID(tenant_id),
                    DefensiveDatasetVersionRow.dataset_id == dataset_id,
                )
            )
            if row is None:
                raise LookupError("Defensive dataset was not found for the authenticated tenant.")
            return _dataset_contract(row)

    async def list_datasets(self, tenant_id: str, limit: int = 100) -> list[DefensiveDatasetVersion]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(DefensiveDatasetVersionRow)
                .where(DefensiveDatasetVersionRow.tenant_id == UUID(tenant_id))
                .order_by(DefensiveDatasetVersionRow.created_at.desc(), DefensiveDatasetVersionRow.dataset_id)
                .limit(safe_limit)
            )
            return [_dataset_contract(row) for row in rows]

    async def samples_for_dataset(
        self, tenant_id: str, dataset_id: str, split: str
    ) -> list[DefensiveDatasetSample]:
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(DefensiveDatasetSampleRow)
                .where(
                    DefensiveDatasetSampleRow.tenant_id == UUID(tenant_id),
                    DefensiveDatasetSampleRow.dataset_id == dataset_id,
                    DefensiveDatasetSampleRow.split == split,
                )
                .order_by(DefensiveDatasetSampleRow.source_record_fingerprint, DefensiveDatasetSampleRow.sample_id)
            )
            return [_sample_contract(row) for row in rows]

    async def upsert_policy(self, policy: DefensiveEvaluationPolicy) -> DefensiveEvaluationPolicy:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(DefensiveEvaluationPolicyRow).where(
                    DefensiveEvaluationPolicyRow.tenant_id == UUID(policy.tenant_id),
                    DefensiveEvaluationPolicyRow.name == policy.name,
                )
            )
            now = datetime.now(timezone.utc)
            values = {
                "enabled": policy.enabled,
                "minimum_precision": policy.minimum_precision,
                "minimum_recall": policy.minimum_recall,
                "maximum_false_positive_rate": policy.maximum_false_positive_rate,
                "minimum_attack_samples": policy.minimum_attack_samples,
                "minimum_benign_samples": policy.minimum_benign_samples,
                "require_test_split": policy.require_test_split,
            }
            if row is None:
                row = DefensiveEvaluationPolicyRow(
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

    async def get_policy(self, tenant_id: str, policy_id: str) -> DefensiveEvaluationPolicy:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(DefensiveEvaluationPolicyRow).where(
                    DefensiveEvaluationPolicyRow.tenant_id == UUID(tenant_id),
                    DefensiveEvaluationPolicyRow.policy_id == policy_id,
                )
            )
            if row is None:
                raise LookupError("Defensive evaluation policy was not found for the authenticated tenant.")
            return _policy_contract(row)

    async def list_policies(self, tenant_id: str, enabled_only: bool = False) -> list[DefensiveEvaluationPolicy]:
        async with self._session_factory() as session:
            statement = select(DefensiveEvaluationPolicyRow).where(
                DefensiveEvaluationPolicyRow.tenant_id == UUID(tenant_id)
            )
            if enabled_only:
                statement = statement.where(DefensiveEvaluationPolicyRow.enabled.is_(True))
            rows = await session.scalars(statement.order_by(DefensiveEvaluationPolicyRow.name))
            return [_policy_contract(row) for row in rows]

    async def persist_evaluation(self, evaluation: DefensiveModelEvaluation) -> tuple[DefensiveModelEvaluation, bool]:
        fingerprint = defensive_evaluation_fingerprint(evaluation)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(DefensiveModelEvaluationRow).where(
                    DefensiveModelEvaluationRow.tenant_id == UUID(evaluation.tenant_id),
                    DefensiveModelEvaluationRow.policy_id == evaluation.policy_id,
                    DefensiveModelEvaluationRow.dataset_id == evaluation.dataset_id,
                    DefensiveModelEvaluationRow.model_id == evaluation.model_id,
                    DefensiveModelEvaluationRow.model_version == evaluation.model_version,
                    DefensiveModelEvaluationRow.evaluation_fingerprint == fingerprint,
                )
            )
            if existing is not None:
                return _evaluation_contract(existing), False
            row = DefensiveModelEvaluationRow(
                evaluation_id=evaluation.evaluation_id,
                tenant_id=UUID(evaluation.tenant_id),
                policy_id=evaluation.policy_id,
                dataset_id=evaluation.dataset_id,
                dataset_version=evaluation.dataset_version,
                dataset_fingerprint=evaluation.dataset_fingerprint,
                model_id=evaluation.model_id,
                model_version=evaluation.model_version,
                evaluated_split=evaluation.evaluated_split,
                true_positive=evaluation.true_positive,
                false_positive=evaluation.false_positive,
                true_negative=evaluation.true_negative,
                false_negative=evaluation.false_negative,
                precision=evaluation.precision,
                recall=evaluation.recall,
                false_positive_rate=evaluation.false_positive_rate,
                status=evaluation.status,
                rejection_reasons=evaluation.rejection_reasons,
                evaluation_fingerprint=fingerprint,
                evaluated_at=evaluation.evaluated_at,
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
                    select(DefensiveModelEvaluationRow).where(
                        DefensiveModelEvaluationRow.tenant_id == UUID(evaluation.tenant_id),
                        DefensiveModelEvaluationRow.policy_id == evaluation.policy_id,
                        DefensiveModelEvaluationRow.dataset_id == evaluation.dataset_id,
                        DefensiveModelEvaluationRow.model_id == evaluation.model_id,
                        DefensiveModelEvaluationRow.model_version == evaluation.model_version,
                        DefensiveModelEvaluationRow.evaluation_fingerprint == fingerprint,
                    )
                )
                if existing is None:
                    raise
                return _evaluation_contract(existing), False
            return _evaluation_contract(row), True

    async def get_evaluation(self, tenant_id: str, evaluation_id: str) -> DefensiveModelEvaluation:
        """Return one immutable evaluation record for its owning tenant only."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(DefensiveModelEvaluationRow).where(
                    DefensiveModelEvaluationRow.tenant_id == UUID(tenant_id),
                    DefensiveModelEvaluationRow.evaluation_id == evaluation_id,
                )
            )
            if row is None:
                raise LookupError("Defensive model evaluation was not found for the authenticated tenant.")
            return _evaluation_contract(row)

    async def list_evaluations(self, tenant_id: str, limit: int = 100) -> list[DefensiveModelEvaluation]:
        safe_limit = max(1, min(limit, 500))
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(DefensiveModelEvaluationRow)
                .where(DefensiveModelEvaluationRow.tenant_id == UUID(tenant_id))
                .order_by(DefensiveModelEvaluationRow.evaluated_at.desc(), DefensiveModelEvaluationRow.evaluation_id)
                .limit(safe_limit)
            )
            return [_evaluation_contract(row) for row in rows]


class RiskScoreThresholdClassifier:
    """Transparent baseline classifier for controlled fixtures only.

    It uses one sanitized numeric `risk_score` feature, deliberately avoids labels and attack-family
    fields, and is included to exercise the evaluator—not to claim a trained detection model.
    """

    model_id = "deterministic-risk-score-baseline"
    model_version = "1.0.0"

    def __init__(self, threshold: float = 0.50) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("risk score threshold must be within [0.0, 1.0].")
        self._threshold = threshold

    def predicts_attack(self, sample: DefensiveDatasetSample) -> bool:
        value = sample.feature_payload.get("risk_score", 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("risk_score must be a numeric sanitized feature for the baseline classifier.")
        return float(value) >= self._threshold


class DefensiveModelEvaluationService:
    """Evaluate an advisory classifier against a tenant's versioned sanitized corpus."""

    def __init__(self, repository: DefensiveEvaluationRepository) -> None:
        self._repository = repository

    async def evaluate(
        self,
        *,
        tenant_id: str,
        policy_id: str,
        dataset_id: str,
        classifier: DefensiveClassifier,
        split: str = "test",
    ) -> DefensiveModelEvaluation:
        if split not in {"validation", "test"}:
            raise ValueError("Only validation or test splits may be evaluated.")
        policy = await self._repository.get_policy(tenant_id, policy_id)
        if not policy.enabled:
            raise PermissionError("Defensive evaluation policy is disabled.")
        if policy.require_test_split and split != "test":
            raise PermissionError("The tenant policy requires held-out test split evaluation.")
        dataset = await self._repository.get_dataset(tenant_id, dataset_id)
        samples = await self._repository.samples_for_dataset(tenant_id, dataset_id, split)
        attack_samples = sum(1 for sample in samples if sample.label == "attack")
        benign_samples = sum(1 for sample in samples if sample.label == "benign")
        if attack_samples < policy.minimum_attack_samples or benign_samples < policy.minimum_benign_samples:
            reasons = []
            if attack_samples < policy.minimum_attack_samples:
                reasons.append(
                    f"minimum_attack_samples={policy.minimum_attack_samples} not met; observed={attack_samples}"
                )
            if benign_samples < policy.minimum_benign_samples:
                reasons.append(
                    f"minimum_benign_samples={policy.minimum_benign_samples} not met; observed={benign_samples}"
                )
            evaluation = self._result(
                tenant_id=tenant_id,
                policy=policy,
                dataset=dataset,
                classifier=classifier,
                split=split,
                true_positive=0,
                false_positive=0,
                true_negative=0,
                false_negative=0,
                status="insufficient_data",
                rejection_reasons=reasons,
            )
            return (await self._repository.persist_evaluation(evaluation))[0]

        true_positive = false_positive = true_negative = false_negative = 0
        for sample in samples:
            predicted_attack = classifier.predicts_attack(sample)
            if sample.label == "attack" and predicted_attack:
                true_positive += 1
            elif sample.label == "attack":
                false_negative += 1
            elif predicted_attack:
                false_positive += 1
            else:
                true_negative += 1

        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        false_positive_rate = false_positive / (false_positive + true_negative) if false_positive + true_negative else 0.0
        rejection_reasons: list[str] = []
        if precision < policy.minimum_precision:
            rejection_reasons.append(f"precision={precision:.6f} below minimum_precision={policy.minimum_precision:.6f}")
        if recall < policy.minimum_recall:
            rejection_reasons.append(f"recall={recall:.6f} below minimum_recall={policy.minimum_recall:.6f}")
        if false_positive_rate > policy.maximum_false_positive_rate:
            rejection_reasons.append(
                f"false_positive_rate={false_positive_rate:.6f} exceeds maximum_false_positive_rate={policy.maximum_false_positive_rate:.6f}"
            )
        evaluation = self._result(
            tenant_id=tenant_id,
            policy=policy,
            dataset=dataset,
            classifier=classifier,
            split=split,
            true_positive=true_positive,
            false_positive=false_positive,
            true_negative=true_negative,
            false_negative=false_negative,
            status="accepted" if not rejection_reasons else "rejected",
            rejection_reasons=rejection_reasons,
        )
        return (await self._repository.persist_evaluation(evaluation))[0]

    @staticmethod
    def _result(
        *,
        tenant_id: str,
        policy: DefensiveEvaluationPolicy,
        dataset: DefensiveDatasetVersion,
        classifier: DefensiveClassifier,
        split: str,
        true_positive: int,
        false_positive: int,
        true_negative: int,
        false_negative: int,
        status: str,
        rejection_reasons: list[str],
    ) -> DefensiveModelEvaluation:
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        false_positive_rate = false_positive / (false_positive + true_negative) if false_positive + true_negative else 0.0
        return DefensiveModelEvaluation(
            tenant_id=tenant_id,
            policy_id=policy.policy_id,
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            dataset_fingerprint=dataset.dataset_fingerprint,
            model_id=classifier.model_id,
            model_version=classifier.model_version,
            evaluated_split=split,
            true_positive=true_positive,
            false_positive=false_positive,
            true_negative=true_negative,
            false_negative=false_negative,
            precision=precision,
            recall=recall,
            false_positive_rate=false_positive_rate,
            status=status,
            rejection_reasons=rejection_reasons,
            advisory_only=True,
            requires_human_approval=True,
            automatic_enforcement=False,
        )
