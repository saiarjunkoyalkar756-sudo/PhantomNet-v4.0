"""Tenant-scoped deterministic correlation rules with bounded evidence and no response authority."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AsyncSessionLocal,
    CorrelationMatchEvidenceRow,
    GovernedCorrelationRuleRow,
    engine,
)
from phantomnet_core.contracts import (
    CorrelationMatchEvidence,
    CorrelationPredicate,
    DetectionRecord,
    EventEnvelope,
    GovernedCorrelationRule,
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
        enabled=row.enabled,
    )


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


async def init_governed_correlation_store() -> None:
    """Provision governed rule and match-evidence tables when migrations are not yet applied."""
    async with engine.begin() as connection:
        await connection.run_sync(GovernedCorrelationRuleRow.__table__.create, checkfirst=True)
        await connection.run_sync(CorrelationMatchEvidenceRow.__table__.create, checkfirst=True)


class GovernedCorrelationRepository:
    """Durable tenant-owned rule and evidence storage with no raw expression interface."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def upsert(self, rule: GovernedCorrelationRule) -> GovernedCorrelationRule:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(GovernedCorrelationRuleRow).where(
                    GovernedCorrelationRuleRow.tenant_id == UUID(rule.tenant_id),
                    GovernedCorrelationRuleRow.name == rule.name,
                )
            )
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc)
            if row is None:
                row = GovernedCorrelationRuleRow(
                    rule_id=rule.rule_id,
                    tenant_id=UUID(rule.tenant_id),
                    version=rule.version,
                    name=rule.name,
                    description=rule.description,
                    event_types=rule.event_types,
                    predicates=[predicate.model_dump(mode="json") for predicate in rule.predicates],
                    severity=rule.severity,
                    mitre_techniques=rule.mitre_techniques,
                    mitre_tactics=rule.mitre_tactics,
                    correlation_key_fields=rule.correlation_key_fields,
                    threshold=rule.threshold,
                    window_seconds=rule.window_seconds,
                    enabled=rule.enabled,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
                session.add(row)
            else:
                row.version = rule.version
                row.description = rule.description
                row.event_types = rule.event_types
                row.predicates = [predicate.model_dump(mode="json") for predicate in rule.predicates]
                row.severity = rule.severity
                row.mitre_techniques = rule.mitre_techniques
                row.mitre_tactics = rule.mitre_tactics
                row.correlation_key_fields = rule.correlation_key_fields
                row.threshold = rule.threshold
                row.window_seconds = rule.window_seconds
                row.enabled = rule.enabled
                row.updated_at = timestamp
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
                    tactic=rule.mitre_tactics[index] if index < len(rule.mitre_tactics) else "unknown",
                    confidence=1.0,
                    rationale="Tenant-owned deterministic correlation rule threshold was met.",
                    evidence_fields=matched_predicates,
                )
                for index, technique in enumerate(rule.mitre_techniques)
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
                },
                mitre_evidence=mitre_evidence,
                tags=["governed-correlation", "threshold-met"],
                automatic_enforcement=False,
            )
            await self._repository.mark_detection(event.tenant_id, rule.rule_id, event.event_id, detection.detection_id)
            detections.append(detection)
        return detections
