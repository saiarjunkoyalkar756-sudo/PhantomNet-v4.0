from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.ai_behavioral_engine.advisory_model import (
    AdvisoryModelAssessmentRepository,
    AdvisoryModelAssessmentService,
    DeterministicAdvisoryProvider,
    OpenAICompatibleAdvisoryProvider,
)
from backend_api.ai_behavioral_engine.defensive_evaluation import (
    DefensiveEvaluationRepository,
    DefensiveModelEvaluationService,
    RiskScoreThresholdClassifier,
    build_dataset_version,
)
from backend_api.shared.database import (
    AdvisoryModelAssessmentRow,
    Base,
    DefensiveModelEvaluationRow,
)
from phantomnet_core.contracts import (
    DefensiveDatasetSample,
    DefensiveDatasetSource,
    DefensiveEvaluationPolicy,
    DetectionRecord,
    IntegratedEvidenceRecord,
)


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"


async def _sessions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False), engine


def _sha(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _source(tenant_id: str = TENANT_ID) -> DefensiveDatasetSource:
    return DefensiveDatasetSource(
        tenant_id=tenant_id,
        name="Controlled BAS risk-score evaluation corpus",
        source_type="controlled_bas",
        source_fingerprint=_sha("phantomnet-controlled-bas-v1"),
        contains_raw_telemetry=False,
        sanitization_attested=True,
    )


def _sample(
    dataset_id: str,
    *,
    split: str,
    label: str,
    risk_score: float,
    index: int,
    tenant_id: str = TENANT_ID,
) -> DefensiveDatasetSample:
    return DefensiveDatasetSample(
        tenant_id=tenant_id,
        dataset_id=dataset_id,
        split=split,
        label=label,
        attack_family="controlled-bas" if label == "attack" else None,
        mitre_techniques=["T1110"] if label == "attack" else [],
        feature_payload={"risk_score": risk_score, "fixture_index": index},
        source_record_fingerprint=_sha(f"{tenant_id}:{dataset_id}:{split}:{label}:{risk_score}:{index}"),
        sanitized=True,
    )


def _samples(dataset_id: str, tenant_id: str = TENANT_ID) -> list[DefensiveDatasetSample]:
    return [
        _sample(dataset_id, split="train", label="attack", risk_score=0.90, index=1, tenant_id=tenant_id),
        _sample(dataset_id, split="train", label="benign", risk_score=0.10, index=2, tenant_id=tenant_id),
        _sample(dataset_id, split="validation", label="attack", risk_score=0.80, index=3, tenant_id=tenant_id),
        _sample(dataset_id, split="validation", label="benign", risk_score=0.20, index=4, tenant_id=tenant_id),
        _sample(dataset_id, split="test", label="attack", risk_score=0.95, index=5, tenant_id=tenant_id),
        _sample(dataset_id, split="test", label="attack", risk_score=0.70, index=6, tenant_id=tenant_id),
        _sample(dataset_id, split="test", label="benign", risk_score=0.15, index=7, tenant_id=tenant_id),
        _sample(dataset_id, split="test", label="benign", risk_score=0.25, index=8, tenant_id=tenant_id),
    ]


def _policy(tenant_id: str = TENANT_ID, **overrides) -> DefensiveEvaluationPolicy:
    return DefensiveEvaluationPolicy(
        tenant_id=tenant_id,
        name="Minimum evidence quality for advisory risk-score model",
        minimum_precision=0.80,
        minimum_recall=0.80,
        maximum_false_positive_rate=0.10,
        minimum_attack_samples=2,
        minimum_benign_samples=2,
        require_test_split=True,
        **overrides,
    )


async def _registered_dataset(repository: DefensiveEvaluationRepository, tenant_id: str = TENANT_ID):
    source, _ = await repository.register_source(_source(tenant_id))
    dataset_id = str(uuid4())
    samples = _samples(dataset_id, tenant_id)
    dataset = build_dataset_version(
        tenant_id=tenant_id,
        source_id=source.source_id,
        name="Controlled BAS risk-score corpus",
        version="1.0.0",
        intended_use="evaluation_only",
        samples=samples,
        dataset_id=dataset_id,
    )
    stored, _ = await repository.register_dataset(dataset, samples)
    return stored, samples


def test_defensive_dataset_contracts_reject_raw_data_unapproved_external_sources_and_enforcement():
    source = _source()
    with pytest.raises(ValidationError, match="raw telemetry"):
        DefensiveDatasetSource.model_validate({**source.model_dump(), "contains_raw_telemetry": True})
    with pytest.raises(ValidationError, match="operator and license approval"):
        DefensiveDatasetSource(
            tenant_id=TENANT_ID,
            name="External corpus without review",
            source_type="external_public",
            source_uri="https://example.invalid/dataset",
            source_fingerprint=_sha("external"),
        )
    with pytest.raises(ValidationError, match="cannot enable enforcement"):
        DefensiveEvaluationPolicy.model_validate({**_policy().model_dump(), "automatic_enforcement": True})


@pytest.mark.asyncio
async def test_sanitized_versioned_dataset_is_tenant_scoped_and_reproducible():
    sessions, engine = await _sessions()
    try:
        repository = DefensiveEvaluationRepository(sessions)
        dataset, samples = await _registered_dataset(repository)
        duplicate, created = await repository.register_dataset(dataset, samples)

        assert created is False
        assert duplicate.dataset_id == dataset.dataset_id
        assert dataset.dataset_fingerprint == build_dataset_version(
            tenant_id=TENANT_ID,
            source_id=dataset.source_id,
            name=dataset.name,
            version=dataset.version,
            intended_use=dataset.intended_use,
            samples=samples,
            dataset_id=dataset.dataset_id,
        ).dataset_fingerprint
        assert dataset.sample_count == 8
        assert dataset.attack_sample_count == 4
        assert dataset.benign_sample_count == 4
        assert dataset.test_split_count == 4
        assert await repository.list_datasets(OTHER_TENANT_ID) == []
        with pytest.raises(LookupError, match="authenticated tenant"):
            await repository.get_dataset(OTHER_TENANT_ID, dataset.dataset_id)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_policy_gated_evaluation_produces_immutable_accepted_metrics_without_enforcement():
    sessions, engine = await _sessions()
    try:
        repository = DefensiveEvaluationRepository(sessions)
        dataset, _ = await _registered_dataset(repository)
        policy = await repository.upsert_policy(_policy())
        service = DefensiveModelEvaluationService(repository)

        evaluation = await service.evaluate(
            tenant_id=TENANT_ID,
            policy_id=policy.policy_id,
            dataset_id=dataset.dataset_id,
            classifier=RiskScoreThresholdClassifier(),
        )
        repeated = await service.evaluate(
            tenant_id=TENANT_ID,
            policy_id=policy.policy_id,
            dataset_id=dataset.dataset_id,
            classifier=RiskScoreThresholdClassifier(),
        )

        assert evaluation.evaluation_id == repeated.evaluation_id
        assert evaluation.status == "accepted"
        assert (evaluation.true_positive, evaluation.false_positive, evaluation.true_negative, evaluation.false_negative) == (2, 0, 2, 0)
        assert evaluation.precision == evaluation.recall == 1.0
        assert evaluation.false_positive_rate == 0.0
        assert evaluation.advisory_only is True
        assert evaluation.requires_human_approval is True
        assert evaluation.automatic_enforcement is False

        async with sessions() as session:
            row = await session.scalar(select(DefensiveModelEvaluationRow))
            assert row is not None
            row.status = "rejected"
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_evaluation_rejects_model_that_fails_policy_metrics():
    sessions, engine = await _sessions()
    try:
        repository = DefensiveEvaluationRepository(sessions)
        dataset, _ = await _registered_dataset(repository)
        policy = await repository.upsert_policy(_policy())
        evaluation = await DefensiveModelEvaluationService(repository).evaluate(
            tenant_id=TENANT_ID,
            policy_id=policy.policy_id,
            dataset_id=dataset.dataset_id,
            classifier=RiskScoreThresholdClassifier(threshold=0.99),
        )

        assert evaluation.status == "rejected"
        assert evaluation.true_positive == 0
        assert evaluation.false_negative == 2
        assert any("recall=" in reason for reason in evaluation.rejection_reasons)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_advisory_assessment_requires_accepted_matching_evaluation_and_linked_evidence():
    sessions, engine = await _sessions()
    try:
        evaluations = DefensiveEvaluationRepository(sessions)
        dataset, _ = await _registered_dataset(evaluations)
        policy = await evaluations.upsert_policy(_policy())
        accepted = await DefensiveModelEvaluationService(evaluations).evaluate(
            tenant_id=TENANT_ID,
            policy_id=policy.policy_id,
            dataset_id=dataset.dataset_id,
            classifier=RiskScoreThresholdClassifier(),
        )
        detection = DetectionRecord(
            detection_id="defensive-evaluation-detection-1",
            rule_id="governed-risk-score-rule",
            rule_version="1.0.0",
            event_id="defensive-evaluation-event-1",
            tenant_id=TENANT_ID,
            severity="high",
            title="High confidence controlled detection",
            evidence={"risk_score": 0.95},
        )
        evidence = IntegratedEvidenceRecord(
            tenant_id=TENANT_ID,
            source_kind="endpoint",
            source_name="controlled-bas",
            source_record_id=detection.event_id,
            observed_at=datetime.now(timezone.utc),
            payload={"risk_score": 0.95},
            tags=["controlled", "sanitized"],
            provenance={"adapter": "test", "read_only": True},
        )
        assessment_repository = AdvisoryModelAssessmentRepository(sessions)
        service = AdvisoryModelAssessmentService(
            evaluations,
            assessment_repository,
            DeterministicAdvisoryProvider(),
        )

        assessment = await service.assess(
            detection=detection,
            evidence=[evidence],
            evaluation_id=accepted.evaluation_id,
        )

        assert assessment.classification == "suspicious"
        assert assessment.recommended_mode == "investigate"
        assert assessment.evidence_ids == [evidence.evidence_id]
        assert assessment.advisory_only is True
        assert assessment.requires_human_approval is True
        assert assessment.automatic_enforcement is False
        async with sessions() as session:
            row = await session.scalar(select(AdvisoryModelAssessmentRow))
            assert row is not None
            row.recommended_mode = "observe"
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()

        rejected = await DefensiveModelEvaluationService(evaluations).evaluate(
            tenant_id=TENANT_ID,
            policy_id=policy.policy_id,
            dataset_id=dataset.dataset_id,
            classifier=RiskScoreThresholdClassifier(threshold=0.99),
        )
        with pytest.raises(PermissionError, match="accepted defensive model evaluation"):
            await service.assess(detection=detection, evidence=[evidence], evaluation_id=rejected.evaluation_id)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_optional_openai_provider_is_mockable_and_uses_a_response_free_strict_schema(monkeypatch):
    monkeypatch.delenv("PHANTOMNET_ADVISORY_MODEL_ENABLED", raising=False)
    assert OpenAICompatibleAdvisoryProvider.from_environment() is None

    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "classification": "suspicious",
                                    "confidence": 0.88,
                                    "reasons": ["Fixture evidence is corroborated."],
                                    "recommended_mode": "investigate",
                                }
                            )
                        }
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleAdvisoryProvider(
            model_id="gpt-5-mini",
            model_version="fixture-1",
            api_key="test-key",
            base_url="https://provider.example/v1",
            client=client,
        )
        detection = DetectionRecord(
            detection_id="provider-fixture-detection",
            rule_id="fixture-rule",
            rule_version="1.0.0",
            event_id="provider-fixture-event",
            tenant_id=TENANT_ID,
            severity="medium",
            title="Provider fixture",
            evidence={},
        )
        evidence = IntegratedEvidenceRecord(
            tenant_id=TENANT_ID,
            source_kind="endpoint",
            source_name="fixture",
            source_record_id=detection.event_id,
            observed_at=datetime.now(timezone.utc),
            payload={"redacted": True},
            tags=["sanitized"],
            provenance={"adapter": "test", "read_only": True},
        )
        result = await provider.assess(detection, [evidence])

    assert result.recommended_mode == "investigate"
    schema = captured["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert {"classification", "confidence", "reasons", "recommended_mode"} == set(schema["properties"])
    assert "action" not in schema["properties"]
    assert "target" not in schema["properties"]
