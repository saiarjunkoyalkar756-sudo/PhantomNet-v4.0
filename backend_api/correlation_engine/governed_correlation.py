"""Tenant-scoped deterministic correlation rules with bounded evidence and no response authority."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AsyncSessionLocal,
    CorrelationMatchEvidenceRow,
    GovernedCorrelationRuleRevisionRow,
    GovernedCorrelationRuleRow,
    engine,
)
from phantomnet_core.contracts import (
    CorrelationMatchEvidence,
    CorrelationPredicate,
    DetectionRecord,
    EventEnvelope,
    GovernedCorrelationFixtureEvaluation,
    GovernedCorrelationRule,
    GovernedCorrelationRuleFixture,
    MitreEvidence,
)


SessionFactory = Callable[[], AsyncSession]


def _rule_contract(row: GovernedCorrelationRuleRow) -> GovernedCorrelationRule:
    return GovernedCorrelationRule(
        rule_id=row.rule_id,
        tenant_id=str(row.tenant_id),
        version=row.version,
        name=row.name,
        description=row.description,
        event_types=list(row.event_types),
        predicates=[CorrelationPredicate.model_validate(predicate) for predicate in row.predicates],
        severity=row.severity,
        mitre_techniques=list(row.mitre_techniques),
        mitre_tactics=list(row.mitre_tactics),
        correlation_key_fields=list(row.correlation_key_fields),
        threshold=row.threshold,
        window_seconds=row.window_seconds,
        suppression_window_seconds=row.suppression_window_seconds,
        enabled=row.enabled,
        automatic_enforcement=False,
    )


def _version_key(version: str) -> tuple[int, int, int]:
    parts = tuple(int(part) for part in version.split("."))
    return (parts[0], parts[1], parts[2] if len(parts) == 3 else 0)


def _rule_definition(rule: GovernedCorrelationRule) -> dict[str, Any]:
    """Return the complete bounded rule definition that a revision attests to."""
    return rule.model_dump(mode="json")


def _definition_fingerprint(rule: GovernedCorrelationRule) -> str:
    canonical = json.dumps(_rule_definition(rule), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(canonical).hexdigest()


def _field_value(event: EventEnvelope, field: str) -> Any:
    if field.startswith("payload."):
        current: Any = event.payload
        path = field.split(".")[1:]
    elif field.startswith("provenance."):
        current = event.provenance
        path = field.split(".")[1:]
    else:
        current = event.model_dump(mode="json")
        path = field.split(".")
    for segment in path:
        if not isinstance(current, Mapping) or segment not in current:
            return None
        current = current[segment]
    return current


def _matches(predicate: CorrelationPredicate, event: EventEnvelope) -> bool:
    actual = _field_value(event, predicate.field)
    if actual is None:
        return False
    expected = predicate.value
    if predicate.operator == "equals":
        return actual == expected
    if predicate.operator == "contains":
        return isinstance(actual, (str, list)) and expected in actual
    if predicate.operator == "gte":
        return isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and actual >= expected
    if predicate.operator == "lte":
        return isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and actual <= expected
    if predicate.operator == "in":
        return isinstance(expected, list) and actual in expected
    return False


def _correlation_key(rule: GovernedCorrelationRule, event: EventEnvelope) -> str:
    values = [_field_value(event, field) for field in rule.correlation_key_fields]
    material = values if values else [event.correlation_id or f"{event.source}:{event.event_type}"]
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def evaluate_fixture(
    rule: GovernedCorrelationRule,
    fixture: GovernedCorrelationRuleFixture,
) -> GovernedCorrelationFixtureEvaluation:
    """Evaluate a bounded fixture deterministically without database writes or response capability."""
    if rule.tenant_id != fixture.tenant_id or rule.rule_id != fixture.rule_id:
        raise ValueError("Fixture tenant and rule ID must exactly match the stored governed rule.")
    ordered_events = sorted(fixture.events, key=lambda event: (event.timestamp, event.event_id))
    windows: dict[str, list[datetime]] = {}
    matched_event_ids: list[str] = []
    detection_event_ids: list[str] = []
    for event in ordered_events:
        if event.event_type not in rule.event_types or not all(_matches(predicate, event) for predicate in rule.predicates):
            continue
        matched_event_ids.append(event.event_id)
        correlation_key = _correlation_key(rule, event)
        cutoff = event.timestamp - timedelta(seconds=rule.window_seconds)
        timestamps = [timestamp for timestamp in windows.get(correlation_key, []) if cutoff <= timestamp <= event.timestamp]
        timestamps.append(event.timestamp)
        windows[correlation_key] = timestamps
        if len(timestamps) >= rule.threshold:
            detection_event_ids.append(event.event_id)
    expected = list(fixture.expected_detection_event_ids)
    return GovernedCorrelationFixtureEvaluation(
        fixture_id=fixture.fixture_id,
        tenant_id=fixture.tenant_id,
        rule_id=rule.rule_id,
        rule_version=rule.version,
        evaluated_event_ids=[event.event_id for event in ordered_events],
        matched_event_ids=matched_event_ids,
        detection_event_ids=detection_event_ids,
        expected_detection_event_ids=expected,
        expectations_met=detection_event_ids == expected,
        automatic_enforcement=False,
    )


async def init_governed_correlation_store() -> None:
    """Provision governed rule, immutable revision, and match-evidence tables when migrations are not yet applied."""
    async with engine.begin() as connection:
        await connection.run_sync(GovernedCorrelationRuleRow.__table__.create, checkfirst=True)
        await connection.run_sync(GovernedCorrelationRuleRevisionRow.__table__.create, checkfirst=True)
        await connection.run_sync(CorrelationMatchEvidenceRow.__table__.create, checkfirst=True)


class GovernedCorrelationRepository:
    """Durable tenant-owned rule and evidence storage with no raw expression interface."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _revision_row(rule: GovernedCorrelationRule, timestamp: datetime) -> GovernedCorrelationRuleRevisionRow:
        return GovernedCorrelationRuleRevisionRow(
            revision_id=str(uuid4()),
            tenant_id=UUID(rule.tenant_id),
            rule_id=rule.rule_id,
            version=rule.version,
            definition_fingerprint=_definition_fingerprint(rule),
            definition=_rule_definition(rule),
            created_at=timestamp,
        )

    async def upsert(self, rule: GovernedCorrelationRule) -> GovernedCorrelationRule:
        """Store an active rule projection and an immutable snapshot for each monotonic definition version."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(GovernedCorrelationRuleRow).where(
                    GovernedCorrelationRuleRow.tenant_id == UUID(rule.tenant_id),
                    GovernedCorrelationRuleRow.name == rule.name,
                )
            )
            timestamp = datetime.now(timezone.utc)
            if row is None:
                stored = rule
                row = GovernedCorrelationRuleRow(
                    rule_id=stored.rule_id,
                    tenant_id=UUID(stored.tenant_id),
                    version=stored.version,
                    name=stored.name,
                    description=stored.description,
                    event_types=stored.event_types,
                    predicates=[predicate.model_dump(mode="json") for predicate in stored.predicates],
                    severity=stored.severity,
                    mitre_techniques=stored.mitre_techniques,
                    mitre_tactics=stored.mitre_tactics,
                    correlation_key_fields=stored.correlation_key_fields,
                    threshold=stored.threshold,
                    window_seconds=stored.window_seconds,
                    suppression_window_seconds=stored.suppression_window_seconds,
                    enabled=stored.enabled,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
                session.add(row)
                await session.flush()
                session.add(self._revision_row(stored, timestamp))
            else:
                current = _rule_contract(row)
                stored = rule.model_copy(update={"rule_id": current.rule_id})
                candidate_fingerprint = _definition_fingerprint(stored)
                existing_revision = await session.scalar(
                    select(GovernedCorrelationRuleRevisionRow).where(
                        GovernedCorrelationRuleRevisionRow.tenant_id == UUID(stored.tenant_id),
                        GovernedCorrelationRuleRevisionRow.rule_id == stored.rule_id,
                        GovernedCorrelationRuleRevisionRow.version == stored.version,
                    )
                )
                if _version_key(stored.version) < _version_key(current.version):
                    raise ValueError("Governed correlation rule versions cannot be decreased.")
                if _version_key(stored.version) == _version_key(current.version):
                    current_fingerprint = _definition_fingerprint(current)
                    if candidate_fingerprint != current_fingerprint:
                        raise ValueError("A changed governed correlation rule definition requires a higher version.")
                    if existing_revision is None:
                        session.add(self._revision_row(current, timestamp))
                    await session.commit()
                    return current
                if existing_revision is not None:
                    if existing_revision.definition_fingerprint != candidate_fingerprint:
                        raise ValueError("A governed correlation rule version is immutable once recorded.")
                    await session.commit()
                    return current
                row.version = stored.version
                row.description = stored.description
                row.event_types = stored.event_types
                row.predicates = [predicate.model_dump(mode="json") for predicate in stored.predicates]
                row.severity = stored.severity
                row.mitre_techniques = stored.mitre_techniques
                row.mitre_tactics = stored.mitre_tactics
                row.correlation_key_fields = stored.correlation_key_fields
                row.threshold = stored.threshold
                row.window_seconds = stored.window_seconds
                row.suppression_window_seconds = stored.suppression_window_seconds
                row.enabled = stored.enabled
                row.updated_at = timestamp
                session.add(self._revision_row(stored, timestamp))
            await session.commit()
            return _rule_contract(row)

    async def list_rules(self, tenant_id: str, enabled_only: bool = False) -> list[GovernedCorrelationRule]:
        async with self._session_factory() as session:
            statement = select(GovernedCorrelationRuleRow).where(
                GovernedCorrelationRuleRow.tenant_id == UUID(tenant_id)
            ).order_by(GovernedCorrelationRuleRow.name)
            if enabled_only:
                statement = statement.where(GovernedCorrelationRuleRow.enabled.is_(True))
            rows = await session.scalars(statement)
            return [_rule_contract(row) for row in rows]

    async def get_rule(self, tenant_id: str, rule_id: str) -> GovernedCorrelationRule:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(GovernedCorrelationRuleRow).where(
                    GovernedCorrelationRuleRow.tenant_id == UUID(tenant_id),
                    GovernedCorrelationRuleRow.rule_id == rule_id,
                )
            )
            if row is None:
                raise LookupError("Governed correlation rule was not found for the authenticated tenant.")
            return _rule_contract(row)

    async def list_revisions(self, tenant_id: str, rule_id: str) -> list[dict[str, Any]]:
        await self.get_rule(tenant_id, rule_id)
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(GovernedCorrelationRuleRevisionRow)
                .where(
                    GovernedCorrelationRuleRevisionRow.tenant_id == UUID(tenant_id),
                    GovernedCorrelationRuleRevisionRow.rule_id == rule_id,
                )
                .order_by(GovernedCorrelationRuleRevisionRow.created_at, GovernedCorrelationRuleRevisionRow.revision_id)
            )
            return [
                {
                    "revision_id": row.revision_id,
                    "rule_id": row.rule_id,
                    "version": row.version,
                    "definition_fingerprint": row.definition_fingerprint,
                    "definition": dict(row.definition),
                    "created_at": row.created_at,
                    "automatic_enforcement": False,
                }
                for row in rows
            ]

    async def evaluate_fixture(self, tenant_id: str, rule_id: str, fixture: GovernedCorrelationRuleFixture) -> GovernedCorrelationFixtureEvaluation:
        rule = await self.get_rule(tenant_id, rule_id)
        return evaluate_fixture(rule, fixture)

    async def record_and_count_match(
        self,
        rule: GovernedCorrelationRule,
        event: EventEnvelope,
        matched_predicates: list[str],
    ) -> CorrelationMatchEvidence:
        correlation_key = _correlation_key(rule, event)
        async with self._session_factory() as session:
            row = await session.scalar(
                select(CorrelationMatchEvidenceRow).where(
                    CorrelationMatchEvidenceRow.tenant_id == UUID(event.tenant_id),
                    CorrelationMatchEvidenceRow.rule_id == rule.rule_id,
                    CorrelationMatchEvidenceRow.event_id == event.event_id,
                )
            )
            if row is None:
                row = CorrelationMatchEvidenceRow(
                    match_id=str(uuid4()),
                    tenant_id=UUID(event.tenant_id),
                    rule_id=rule.rule_id,
                    event_id=event.event_id,
                    correlation_key=correlation_key,
                    matched_predicates=matched_predicates,
                    evaluated_at=event.timestamp,
                    detection_id=None,
                )
                session.add(row)
                await session.flush()
            cutoff = event.timestamp - timedelta(seconds=rule.window_seconds)
            match_count = await session.scalar(
                select(func.count(CorrelationMatchEvidenceRow.id)).where(
                    CorrelationMatchEvidenceRow.tenant_id == UUID(event.tenant_id),
                    CorrelationMatchEvidenceRow.rule_id == rule.rule_id,
                    CorrelationMatchEvidenceRow.correlation_key == correlation_key,
                    CorrelationMatchEvidenceRow.evaluated_at >= cutoff,
                    CorrelationMatchEvidenceRow.evaluated_at <= event.timestamp,
                )
            )
            await session.commit()
            return CorrelationMatchEvidence(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                tenant_id=event.tenant_id,
                event_id=event.event_id,
                correlation_key=correlation_key,
                match_count=int(match_count or 0),
                threshold=rule.threshold,
                window_seconds=rule.window_seconds,
                matched_predicates=matched_predicates,
                evaluated_at=event.timestamp,
                automatic_enforcement=False,
            )

    async def mark_detection(self, tenant_id: str, rule_id: str, event_id: str, detection_id: str) -> None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(CorrelationMatchEvidenceRow).where(
                    CorrelationMatchEvidenceRow.tenant_id == UUID(tenant_id),
                    CorrelationMatchEvidenceRow.rule_id == rule_id,
                    CorrelationMatchEvidenceRow.event_id == event_id,
                )
            )
            if row is None:
                raise LookupError("Correlation match evidence was not found for the tenant event.")
            row.detection_id = detection_id
            await session.commit()

    async def quality_summary(self, tenant_id: str) -> list[dict[str, Any]]:
        async with self._session_factory() as session:
            rules = await session.scalars(
                select(GovernedCorrelationRuleRow)
                .where(GovernedCorrelationRuleRow.tenant_id == UUID(tenant_id))
                .order_by(GovernedCorrelationRuleRow.name)
            )
            summaries: list[dict[str, Any]] = []
            for rule in rules:
                match_count = await session.scalar(
                    select(func.count(CorrelationMatchEvidenceRow.id)).where(
                        CorrelationMatchEvidenceRow.tenant_id == UUID(tenant_id),
                        CorrelationMatchEvidenceRow.rule_id == rule.rule_id,
                    )
                )
                detection_count = await session.scalar(
                    select(func.count(CorrelationMatchEvidenceRow.id)).where(
                        CorrelationMatchEvidenceRow.tenant_id == UUID(tenant_id),
                        CorrelationMatchEvidenceRow.rule_id == rule.rule_id,
                        CorrelationMatchEvidenceRow.detection_id.is_not(None),
                    )
                )
                last_matched_at = await session.scalar(
                    select(func.max(CorrelationMatchEvidenceRow.evaluated_at)).where(
                        CorrelationMatchEvidenceRow.tenant_id == UUID(tenant_id),
                        CorrelationMatchEvidenceRow.rule_id == rule.rule_id,
                    )
                )
                if last_matched_at is not None:
                    last_matched_at = (
                        last_matched_at.replace(tzinfo=timezone.utc)
                        if last_matched_at.tzinfo is None
                        else last_matched_at.astimezone(timezone.utc)
                    )
                summaries.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "severity": rule.severity,
                    "match_count": int(match_count or 0),
                    "detection_count": int(detection_count or 0),
                    "last_matched_at": last_matched_at,
                })
            return summaries

    async def mitre_coverage_summary(self, tenant_id: str) -> dict[str, Any]:
        rules = await self.list_rules(tenant_id)
        technique_counts: dict[str, int] = {}
        tactic_counts: dict[str, int] = {}
        enabled_rule_count = 0
        for rule in rules:
            if rule.enabled:
                enabled_rule_count += 1
            for technique, tactic in zip(rule.mitre_techniques, rule.mitre_tactics, strict=True):
                technique_counts[technique] = technique_counts.get(technique, 0) + 1
                tactic_counts[tactic] = tactic_counts.get(tactic, 0) + 1
        return {
            "tenant_id": tenant_id,
            "rule_count": len(rules),
            "enabled_rule_count": enabled_rule_count,
            "technique_coverage": dict(sorted(technique_counts.items())),
            "tactic_coverage": dict(sorted(tactic_counts.items())),
            "automatic_enforcement": False,
        }


class GovernedCorrelationEngine:
    """Evaluate only stored tenant rules and emit advisory detections after their bounded threshold is met."""

    def __init__(self, repository: GovernedCorrelationRepository) -> None:
        self._repository = repository

    async def evaluate_event(self, event: EventEnvelope) -> list[DetectionRecord]:
        detections: list[DetectionRecord] = []
        for rule in await self._repository.list_rules(event.tenant_id, enabled_only=True):
            if event.event_type not in rule.event_types:
                continue
            if not all(_matches(predicate, event) for predicate in rule.predicates):
                continue
            matched_predicates = [predicate.field for predicate in rule.predicates]
            evidence = await self._repository.record_and_count_match(rule, event, matched_predicates)
            if evidence.match_count < rule.threshold:
                continue
            mitre_evidence = [
                MitreEvidence(
                    technique_id=technique,
                    tactic=tactic,
                    confidence=1.0,
                    rationale="Tenant-owned deterministic correlation rule threshold was met.",
                    evidence_fields=matched_predicates,
                )
                for technique, tactic in zip(rule.mitre_techniques, rule.mitre_tactics, strict=True)
            ]
            detection = DetectionRecord(
                detection_id=f"correlation-{event.event_id}-{rule.rule_id}",
                rule_id=rule.rule_id,
                rule_version=rule.version,
                event_id=event.event_id,
                tenant_id=event.tenant_id,
                correlation_id=event.correlation_id,
                severity=rule.severity,
                title=rule.name,
                evidence={
                    "correlation": evidence.model_dump(mode="json"),
                    "rule_description": rule.description,
                    "rule_definition_fingerprint": _definition_fingerprint(rule),
                    "alert_suppression_window_seconds": rule.suppression_window_seconds,
                },
                mitre_evidence=mitre_evidence,
                tags=["governed-correlation", "threshold-met"],
                automatic_enforcement=False,
            )
            await self._repository.mark_detection(event.tenant_id, rule.rule_id, event.event_id, detection.detection_id)
            detections.append(detection)
        return detections
