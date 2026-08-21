"""Canonical contracts shared across PhantomNet telemetry, detection, and analyst workflows."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONTRACT_VERSION = "1.0.0"
MITRE_TECHNIQUE_PATTERN = re.compile(r"^T\d{4}(?:\.\d{3})?$")


class EventEnvelope(BaseModel):
    """A versioned, tenant-scoped event record with immutable correlation metadata."""

    schema_version: str = CONTRACT_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    source: str
    event_type: str
    severity: Literal["informational", "low", "medium", "high", "critical"] = "informational"
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def payload_fingerprint(self) -> str:
        """Produce a deterministic fingerprint without asserting tamper-proof storage."""
        canonical = repr(sorted(self.payload.items())).encode("utf-8")
        return sha256(canonical).hexdigest()


class MitreEvidence(BaseModel):
    """A bounded, analyst-readable ATT&CK mapping produced by a governed rule."""

    technique_id: str
    tactic: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_fields: List[str] = Field(default_factory=list)

    @field_validator("technique_id")
    @classmethod
    def validate_technique_id(cls, value: str) -> str:
        normalized = value.upper()
        if not MITRE_TECHNIQUE_PATTERN.fullmatch(normalized):
            raise ValueError("MITRE technique_id must use T#### or T####.### format")
        return normalized


class DetectionRule(BaseModel):
    """A governed, versioned detection definition with testable expected outcomes."""

    rule_id: str
    version: str
    name: str
    description: str
    enabled: bool = True
    event_types: List[str] = Field(default_factory=list)
    severity: Literal["informational", "low", "medium", "high", "critical"] = "medium"
    threshold: int = Field(default=1, ge=1)
    window_seconds: int = Field(default=300, ge=1)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    mitre_techniques: List[str] = Field(default_factory=list)
    mitre_tactics: List[str] = Field(default_factory=list)
    expected_outcome: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if value.count(".") < 1:
            raise ValueError("rule version must be a dotted version string")
        return value

    @field_validator("mitre_techniques")
    @classmethod
    def validate_mitre_techniques(cls, values: List[str]) -> List[str]:
        normalized = [value.upper() for value in values]
        invalid = [value for value in normalized if not MITRE_TECHNIQUE_PATTERN.fullmatch(value)]
        if invalid:
            raise ValueError("MITRE techniques must use T#### or T####.### format")
        return normalized


class DetectionRecord(BaseModel):
    """A versioned, tenant-scoped detection result produced from a canonical event."""

    schema_version: str = CONTRACT_VERSION
    detection_id: str = Field(default_factory=lambda: str(uuid4()))
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rule_id: str
    rule_version: str
    event_id: str
    tenant_id: str
    correlation_id: Optional[str] = None
    severity: Literal["informational", "low", "medium", "high", "critical"]
    title: str
    status: Literal["detected", "suppressed"] = "detected"
    evidence: Dict[str, Any] = Field(default_factory=dict)
    mitre_evidence: List[MitreEvidence] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    automatic_enforcement: bool = False

    @field_validator("detected_at")
    @classmethod
    def require_timezone_aware_detected_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AlertRecord(BaseModel):
    """Tenant-scoped analyst workflow state derived from one or more governed detections."""

    schema_version: str = CONTRACT_VERSION
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    detection_ids: List[str] = Field(min_length=1)
    correlation_id: Optional[str] = None
    title: str
    severity: Literal["informational", "low", "medium", "high", "critical"]
    status: Literal["new", "triaged", "in_progress", "resolved", "closed", "suppressed"] = "new"
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    occurrence_count: int = Field(default=1, ge=1)
    suppression_key: str
    suppressed_by_alert_id: Optional[str] = None
    mitre_evidence: List[MitreEvidence] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    case_id: Optional[str] = None
    triaged_by: Optional[str] = None

    @field_validator("first_seen", "last_seen")
    @classmethod
    def require_timezone_aware_alert_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class CaseRecord(BaseModel):
    """A tenant-scoped investigation case linked to one or more analyst alerts."""

    schema_version: str = CONTRACT_VERSION
    case_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    alert_ids: List[str] = Field(min_length=1)
    title: str
    severity: Literal["informational", "low", "medium", "high", "critical"]
    status: Literal["new", "triaged", "in_progress", "resolved", "closed"] = "new"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    assigned_to: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_timezone_aware_case_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class PlaybookRunRecord(BaseModel):
    """A case-bound playbook lifecycle record; state changes never execute containment directly."""

    schema_version: str = CONTRACT_VERSION
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    case_id: str
    playbook_id: str
    playbook_version: str
    status: Literal[
        "requested",
        "awaiting_approval",
        "approved",
        "running",
        "completed",
        "failed",
        "cancelled",
    ] = "requested"
    requires_approval: bool = True
    requested_by: str
    approved_by: Optional[str] = None
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("requested_at", "started_at", "completed_at")
    @classmethod
    def require_timezone_aware_playbook_timestamp(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class HostAssetRecord(BaseModel):
    """Tenant-scoped endpoint inventory evidence from an agent or read-only endpoint integration."""

    schema_version: str = CONTRACT_VERSION
    asset_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    agent_id: str = Field(min_length=1, max_length=128)
    hostname: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=80)
    os_version: Optional[str] = Field(default=None, max_length=160)
    ip_addresses: List[str] = Field(default_factory=list, max_length=32)
    software: List[Dict[str, str]] = Field(default_factory=list, max_length=2048)
    tags: List[str] = Field(default_factory=list, max_length=64)
    source: Literal["phantomnet-agent", "wazuh"]
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("last_seen")
    @classmethod
    def require_timezone_aware_asset_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class IntegrityObservation(BaseModel):
    """A host integrity observation that records evidence without changing the endpoint."""

    schema_version: str = CONTRACT_VERSION
    observation_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    asset_id: str
    agent_id: str = Field(min_length=1, max_length=128)
    source_event_id: str = Field(min_length=1, max_length=255)
    source: Literal["phantomnet-agent", "wazuh"]
    check_type: Literal["file", "process", "registry", "configuration"]
    status: Literal["baseline_match", "modified", "missing", "error"]
    severity: Literal["informational", "low", "medium", "high", "critical"]
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    path: Optional[str] = Field(default=None, max_length=2048)
    observed_hash: Optional[str] = Field(default=None, max_length=128)
    expected_hash: Optional[str] = Field(default=None, max_length=128)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    automatic_enforcement: bool = False

    @field_validator("observed_at")
    @classmethod
    def require_timezone_aware_integrity_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class WazuhForwarderRecord(BaseModel):
    """A tenant-bound, telemetry-only Wazuh-compatible forwarder registration."""

    schema_version: str = CONTRACT_VERSION
    forwarder_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    name: str = Field(min_length=3, max_length=120)
    status: Literal["active", "revoked"] = "active"
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: Optional[datetime] = None
    last_sequence: int = Field(default=0, ge=0)
    automatic_enforcement: bool = False

    @field_validator("created_at", "last_seen_at")
    @classmethod
    def require_timezone_aware_forwarder_timestamp(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class WazuhTelemetryBatch(BaseModel):
    """A bounded, ordered batch accepted only from its registered tenant-bound forwarder."""

    batch_id: str = Field(min_length=8, max_length=128)
    sequence: int = Field(ge=1)
    alerts: List[Dict[str, Any]] = Field(min_length=1, max_length=250)


class IntegratedEvidenceRecord(BaseModel):
    """Tenant-owned read-only evidence from an asset, endpoint, Wazuh, identity, intelligence, or graph source."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    source_kind: Literal["asset", "endpoint", "wazuh", "identity", "intelligence", "graph"]
    source_name: str = Field(min_length=2, max_length=120)
    source_record_id: str = Field(min_length=1, max_length=255)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, max_length=32)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    read_only: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_integrated_evidence_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("observed_at", "collected_at")
    @classmethod
    def require_timezone_aware_evidence_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("read_only")
    @classmethod
    def require_read_only_evidence(cls, value: bool) -> bool:
        if not value:
            raise ValueError("integrated evidence must remain read-only.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def prohibit_evidence_automatic_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("integrated evidence cannot enable automatic enforcement.")
        return value

    @model_validator(mode="after")
    def require_read_only_provenance(self) -> "IntegratedEvidenceRecord":
        if self.provenance.get("read_only") is not True:
            raise ValueError("integrated evidence provenance must explicitly attest read_only=true.")
        canonical = json.dumps(self.payload, sort_keys=True, separators=(",", ":"), default=str)
        if len(canonical.encode("utf-8")) > 65_536:
            raise ValueError("integrated evidence payload exceeds the 64 KiB safety limit.")
        return self

    def payload_fingerprint(self) -> str:
        material = {
            "payload": self.payload,
            "provenance": self.provenance,
            "source_kind": self.source_kind,
            "source_name": self.source_name,
            "source_record_id": self.source_record_id,
        }
        canonical = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return sha256(canonical).hexdigest()


class ContainmentRequest(BaseModel):
    """A tenant-scoped high-impact response request that cannot execute before approval."""

    schema_version: str = CONTRACT_VERSION
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    action: Literal["isolate_endpoint", "release_endpoint", "block_indicator", "rollback_indicator_block", "remediate_configuration"]
    target: str = Field(min_length=1, max_length=255)
    asset_id: Optional[str] = None
    playbook_id: Optional[str] = None
    requested_by: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["requested", "approved", "rejected", "executing", "verified", "failed", "rolled_back"] = "requested"
    idempotency_key: str = Field(min_length=16, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    automatic_enforcement: bool = False

    @field_validator("requested_at")
    @classmethod
    def require_timezone_aware_containment_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class ContainmentApproval(BaseModel):
    """A durable human approval or rejection attached to one containment request."""

    approval_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    tenant_id: str
    decision: Literal["approved", "rejected"]
    decided_by: str
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("decided_at")
    @classmethod
    def require_timezone_aware_approval_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class RemediationPlaybookDefinition(BaseModel):
    """A bounded ordered response definition; all high-impact steps remain approval-gated."""

    playbook_id: str
    version: str
    name: str
    actions: List[Literal["isolate_endpoint", "release_endpoint", "block_indicator", "rollback_indicator_block", "remediate_configuration"]] = Field(min_length=1, max_length=10)
    requires_approval: bool = True
    rollback_action: Optional[Literal["release_endpoint", "rollback_indicator_block"]] = None


class ContainmentExecutionEvidence(BaseModel):
    """Adapter outcome and verification evidence for one governed response execution."""

    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    tenant_id: str
    approval_id: str
    adapter: str
    status: Literal["verified", "failed", "rolled_back"]
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verification: Dict[str, Any] = Field(default_factory=dict)
    rollback_available: bool = False
    rolled_back: bool = False
    audit_record_hash: Optional[str] = None

    @field_validator("executed_at")
    @classmethod
    def require_timezone_aware_execution_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class BrokerDeliveryMetadata(BaseModel):
    """Immutable broker coordinates for one canonical delivery; used for idempotent failure receipts."""

    schema_version: str = CONTRACT_VERSION
    topic: str = Field(min_length=1, max_length=255)
    partition: int = Field(ge=0)
    offset: int = Field(ge=0)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("received_at")
    @classmethod
    def require_timezone_aware_delivery_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class IngestionDeadLetterRecord(BaseModel):
    """Durable canonical ingestion failure evidence; replay remains an analyst-controlled operation."""

    schema_version: str = CONTRACT_VERSION
    dead_letter_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: Optional[str] = None
    event_id: Optional[str] = None
    delivery: BrokerDeliveryMetadata
    message_hash: str = Field(min_length=64, max_length=64)
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_code: str = Field(min_length=1, max_length=120)
    error_type: str = Field(min_length=1, max_length=120)
    status: Literal["open", "replayed", "discarded"] = "open"
    attempt_count: int = Field(default=1, ge=1)
    first_failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    replayed_at: Optional[datetime] = None
    replayed_by: Optional[str] = None

    @field_validator("first_failed_at", "last_failed_at", "replayed_at")
    @classmethod
    def require_timezone_aware_dead_letter_timestamp(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("message_hash")
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ValueError("message_hash must be a lowercase SHA-256 hexadecimal digest.")
        return value


class CorrelationPredicate(BaseModel):
    """One bounded structured comparison over a canonical event field; never a raw query expression."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1, max_length=128)
    operator: Literal["equals", "contains", "gte", "lte", "in"]
    value: Any

    @field_validator("field")
    @classmethod
    def validate_field_path(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]{0,127}", value) or "__" in value:
            raise ValueError("predicate field must be a bounded dot-delimited canonical path.")
        return value

    @field_validator("value")
    @classmethod
    def validate_literal_value(cls, value: Any) -> Any:
        scalar = (str, int, float, bool)
        if isinstance(value, scalar):
            return value
        if isinstance(value, list) and 1 <= len(value) <= 100 and all(isinstance(item, scalar) for item in value):
            return value
        raise ValueError("predicate value must be a scalar or a bounded list of scalars.")


class GovernedCorrelationRule(BaseModel):
    """A tenant-owned deterministic correlation rule with advisory detection output only."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = CONTRACT_VERSION
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    version: str = Field(min_length=3, max_length=40)
    name: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=3, max_length=1000)
    event_types: List[str] = Field(min_length=1, max_length=32)
    predicates: List[CorrelationPredicate] = Field(min_length=1, max_length=10)
    severity: Literal["informational", "low", "medium", "high", "critical"]
    mitre_techniques: List[str] = Field(min_length=1, max_length=16)
    mitre_tactics: List[str] = Field(min_length=1, max_length=16)
    correlation_key_fields: List[str] = Field(default_factory=list, max_length=5)
    threshold: int = Field(default=1, ge=1, le=100)
    window_seconds: int = Field(default=300, ge=1, le=86_400)
    suppression_window_seconds: int = Field(default=900, ge=0, le=86_400)
    enabled: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("version")
    @classmethod
    def validate_governed_rule_version(cls, value: str) -> str:
        if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value):
            raise ValueError("governed rule version must be a dotted numeric version.")
        return value

    @field_validator("mitre_techniques")
    @classmethod
    def validate_governed_rule_mitre_techniques(cls, values: List[str]) -> List[str]:
        normalized = [value.upper() for value in values]
        if any(not MITRE_TECHNIQUE_PATTERN.fullmatch(value) for value in normalized):
            raise ValueError("MITRE techniques must use T#### or T####.### format")
        return normalized

    @field_validator("event_types", "correlation_key_fields")
    @classmethod
    def validate_canonical_field_names(cls, values: List[str]) -> List[str]:
        for value in values:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]{0,127}", value) or "__" in value:
                raise ValueError("event types and correlation key fields must be bounded canonical names.")
        return values

    @model_validator(mode="after")
    def require_one_to_one_mitre_mapping(self) -> "GovernedCorrelationRule":
        if len(self.mitre_techniques) != len(self.mitre_tactics):
            raise ValueError("governed rules require exactly one MITRE tactic for each technique.")
        return self


class CorrelationMatchEvidence(BaseModel):
    """Bounded evidence that a tenant-owned rule matched canonical telemetry; it has no response fields."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_version: str
    tenant_id: str
    event_id: str
    correlation_key: str
    match_count: int = Field(ge=1)
    threshold: int = Field(ge=1)
    window_seconds: int = Field(ge=1)
    matched_predicates: List[str] = Field(default_factory=list, max_length=10)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    automatic_enforcement: bool = False

    @field_validator("evaluated_at")
    @classmethod
    def require_timezone_aware_correlation_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class GovernedCorrelationRuleFixture(BaseModel):
    """A bounded, tenant-scoped offline corpus for deterministic advisory rule evaluation."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    rule_id: str
    events: List[EventEnvelope] = Field(min_length=1, max_length=500)
    expected_detection_event_ids: List[str] = Field(default_factory=list, max_length=500)
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_fixture_tenant_id(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @model_validator(mode="after")
    def require_tenant_bound_unique_fixture_events(self) -> "GovernedCorrelationRuleFixture":
        event_ids = [event.event_id for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("fixture event IDs must be unique.")
        if any(event.tenant_id != self.tenant_id for event in self.events):
            raise ValueError("fixture events must belong to the fixture tenant.")
        if any(event_id not in event_ids for event_id in self.expected_detection_event_ids):
            raise ValueError("fixture expected detection IDs must reference fixture events.")
        return self


class GovernedCorrelationFixtureEvaluation(BaseModel):
    """Read-only deterministic evaluation output; it has no containment or response authority."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    tenant_id: str
    rule_id: str
    rule_version: str
    evaluated_event_ids: List[str] = Field(default_factory=list)
    matched_event_ids: List[str] = Field(default_factory=list)
    detection_event_ids: List[str] = Field(default_factory=list)
    expected_detection_event_ids: List[str] = Field(default_factory=list)
    expectations_met: bool
    automatic_enforcement: bool = False


class ResponseAutomationPolicy(BaseModel):
    """A tenant-owned policy that may create a containment request but can never execute it automatically."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    name: str = Field(min_length=3, max_length=160)
    enabled: bool = True
    trigger_rule_ids: List[str] = Field(default_factory=list, max_length=32)
    minimum_severity: Literal["informational", "low", "medium", "high", "critical"] = "high"
    action: Literal["isolate_endpoint", "block_indicator", "remediate_configuration"]
    target: str = Field(min_length=1, max_length=255)
    asset_id: Optional[str] = Field(default=None, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    automatic_enforcement: bool = False

    @field_validator("requires_approval")
    @classmethod
    def require_response_policy_approval(cls, value: bool) -> bool:
        if not value:
            raise ValueError("response automation policies must require human approval.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_response_policy_automatic_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("response automation policies cannot enable automatic enforcement.")
        return value

    @field_validator("tenant_id")
    @classmethod
    def validate_response_policy_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("parameters")
    @classmethod
    def validate_response_policy_parameters(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if len(value) > 32:
            raise ValueError("response policy parameters are limited to 32 entries.")
        if any(not isinstance(key, str) or len(key) > 128 for key in value):
            raise ValueError("response policy parameter keys must be bounded strings.")
        return value


class AutonomousDefensePolicy(BaseModel):
    """A tenant-owned authority policy for evidence-grounded autonomous defense decisions.

    Policies can record investigation decisions or create an approval-required containment proposal.
    They can never dispatch an adapter, bypass an approval, or mark enforcement as automatic.
    """

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    name: str = Field(min_length=3, max_length=160)
    enabled: bool = True
    trigger_rule_ids: List[str] = Field(default_factory=list, max_length=32)
    minimum_severity: Literal["informational", "low", "medium", "high", "critical"] = "high"
    decision_mode: Literal["observe", "investigate", "propose_containment"] = "investigate"
    minimum_confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    minimum_evidence_count: int = Field(default=1, ge=1, le=16)
    required_evidence_kinds: List[Literal["asset", "endpoint", "wazuh", "identity", "intelligence", "graph"]] = Field(default_factory=list, max_length=6)
    cooldown_seconds: int = Field(default=300, ge=60, le=86_400)
    max_decisions_per_hour: int = Field(default=12, ge=1, le=120)
    containment_action: Optional[Literal["isolate_endpoint", "block_indicator", "remediate_configuration"]] = None
    target: Optional[str] = Field(default=None, min_length=1, max_length=255)
    asset_id: Optional[str] = Field(default=None, max_length=255)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_autonomous_policy_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("requires_approval")
    @classmethod
    def require_autonomous_policy_approval(cls, value: bool) -> bool:
        if not value:
            raise ValueError("autonomous defense policies must retain human approval for containment.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_autonomous_policy_automatic_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("autonomous defense policies cannot enable automatic high-impact enforcement.")
        return value

    @field_validator("parameters")
    @classmethod
    def validate_autonomous_policy_parameters(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if len(value) > 32:
            raise ValueError("autonomous policy parameters are limited to 32 entries.")
        if any(not isinstance(key, str) or len(key) > 128 for key in value):
            raise ValueError("autonomous policy parameter keys must be bounded strings.")
        return value

    @model_validator(mode="after")
    def validate_autonomous_authority_scope(self) -> "AutonomousDefensePolicy":
        has_containment_scope = self.containment_action is not None or self.target is not None or self.asset_id is not None
        if self.decision_mode == "propose_containment":
            if self.containment_action is None or self.target is None:
                raise ValueError("containment proposals require an explicit containment_action and target.")
        elif has_containment_scope:
            raise ValueError("only propose_containment policies may define containment scope.")
        if len(set(self.required_evidence_kinds)) != len(self.required_evidence_kinds):
            raise ValueError("required_evidence_kinds must not contain duplicates.")
        return self


class AutonomousDefenseDecision(BaseModel):
    """Immutable, evidence-grounded autonomous defense decision with no adapter authority."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    policy_id: str
    detection_id: str
    rule_id: str
    severity: Literal["informational", "low", "medium", "high", "critical"]
    confidence: float = Field(ge=0.0, le=1.0)
    decision_mode: Literal["observe", "investigate", "propose_containment"]
    outcome: Literal["decision_recorded", "containment_proposed", "refused", "rate_limited"]
    evidence_ids: List[str] = Field(default_factory=list, max_length=16)
    evidence_kinds: List[Literal["asset", "endpoint", "wazuh", "identity", "intelligence", "graph"]] = Field(default_factory=list, max_length=6)
    reasons: List[str] = Field(default_factory=list, min_length=1, max_length=12)
    containment_request_id: Optional[str] = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requires_human_approval: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_autonomous_decision_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("decided_at")
    @classmethod
    def require_timezone_aware_autonomous_decision_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("requires_human_approval")
    @classmethod
    def require_autonomous_decision_human_approval(cls, value: bool) -> bool:
        if not value:
            raise ValueError("autonomous decisions must retain human approval for containment.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_autonomous_decision_automatic_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("autonomous decisions cannot claim automatic high-impact enforcement.")
        return value

    @model_validator(mode="after")
    def validate_decision_outcome(self) -> "AutonomousDefenseDecision":
        if self.outcome == "containment_proposed" and not self.containment_request_id:
            raise ValueError("containment_proposed decisions require a containment_request_id.")
        if self.outcome != "containment_proposed" and self.containment_request_id is not None:
            raise ValueError("only containment_proposed decisions may reference a containment request.")
        if self.decision_mode != "propose_containment" and self.outcome == "containment_proposed":
            raise ValueError("only propose_containment decisions may create a containment proposal.")
        return self


class DefensiveDatasetSource(BaseModel):
    """Operator-approved provenance for a sanitized defensive dataset source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    name: str = Field(min_length=3, max_length=160)
    source_type: Literal["controlled_bas", "operator_uploaded", "external_public", "tenant_sanitized"]
    source_uri: Optional[str] = Field(default=None, max_length=1024)
    source_fingerprint: str = Field(min_length=64, max_length=64)
    license_reference: Optional[str] = Field(default=None, max_length=1024)
    operator_approved: bool = False
    license_reviewed: bool = False
    contains_raw_telemetry: bool = False
    sanitization_attested: bool = True
    approved_by: Optional[str] = Field(default=None, min_length=3, max_length=160)
    approved_at: Optional[datetime] = None
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_defensive_dataset_source_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("source_fingerprint")
    @classmethod
    def validate_defensive_dataset_source_fingerprint(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("source_fingerprint must be a SHA-256 hexadecimal digest.")
        return normalized

    @field_validator("approved_at")
    @classmethod
    def normalize_defensive_dataset_source_approval_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_defensive_dataset_source_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("defensive dataset sources cannot enable enforcement.")
        return value

    @model_validator(mode="after")
    def validate_defensive_dataset_source_governance(self) -> "DefensiveDatasetSource":
        if self.contains_raw_telemetry:
            raise ValueError("raw telemetry cannot enter the defensive dataset registry.")
        if not self.sanitization_attested:
            raise ValueError("defensive dataset sources require an explicit sanitization attestation.")
        if self.source_type in {"external_public", "operator_uploaded", "tenant_sanitized"}:
            if not self.operator_approved or not self.license_reviewed or not self.approved_by or self.approved_at is None:
                raise ValueError("external, uploaded, and tenant-sanitized sources require recorded operator and license approval.")
        if self.source_type == "external_public" and not self.source_uri:
            raise ValueError("external public sources require a source_uri.")
        return self


class DefensiveDatasetVersion(BaseModel):
    """Versioned, sanitized corpus metadata; it has no live telemetry or response authority."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    source_id: str
    name: str = Field(min_length=3, max_length=160)
    version: str = Field(min_length=3, max_length=40)
    dataset_fingerprint: str = Field(min_length=64, max_length=64)
    intended_use: Literal["evaluation_only", "advisory_calibration"] = "evaluation_only"
    sample_count: int = Field(ge=0, le=10_000_000)
    attack_sample_count: int = Field(ge=0, le=10_000_000)
    benign_sample_count: int = Field(ge=0, le=10_000_000)
    training_split_count: int = Field(default=0, ge=0, le=10_000_000)
    validation_split_count: int = Field(default=0, ge=0, le=10_000_000)
    test_split_count: int = Field(default=0, ge=0, le=10_000_000)
    contains_raw_telemetry: bool = False
    sanitization_attested: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_defensive_dataset_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("version")
    @classmethod
    def validate_defensive_dataset_version(cls, value: str) -> str:
        if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value):
            raise ValueError("dataset version must be a dotted numeric version.")
        return value

    @field_validator("dataset_fingerprint")
    @classmethod
    def validate_defensive_dataset_fingerprint(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("dataset_fingerprint must be a SHA-256 hexadecimal digest.")
        return normalized

    @field_validator("created_at")
    @classmethod
    def normalize_defensive_dataset_created_at(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_defensive_dataset_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("defensive datasets cannot enable enforcement.")
        return value

    @model_validator(mode="after")
    def validate_defensive_dataset_counts(self) -> "DefensiveDatasetVersion":
        if self.contains_raw_telemetry or not self.sanitization_attested:
            raise ValueError("defensive datasets must be sanitized and must not retain raw telemetry.")
        if self.attack_sample_count + self.benign_sample_count != self.sample_count:
            raise ValueError("attack and benign counts must equal sample_count.")
        if self.training_split_count + self.validation_split_count + self.test_split_count != self.sample_count:
            raise ValueError("dataset split counts must equal sample_count.")
        return self


class DefensiveDatasetSample(BaseModel):
    """A minimized labelled sample used only for evaluation or advisory calibration."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    dataset_id: str
    split: Literal["train", "validation", "test"]
    label: Literal["benign", "attack"]
    attack_family: Optional[str] = Field(default=None, min_length=2, max_length=100)
    mitre_techniques: List[str] = Field(default_factory=list, max_length=16)
    feature_payload: Dict[str, Any] = Field(default_factory=dict)
    source_record_fingerprint: str = Field(min_length=64, max_length=64)
    sanitized: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_defensive_sample_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("mitre_techniques")
    @classmethod
    def validate_defensive_sample_mitre(cls, values: List[str]) -> List[str]:
        normalized = [value.upper() for value in values]
        if any(not MITRE_TECHNIQUE_PATTERN.fullmatch(value) for value in normalized):
            raise ValueError("MITRE techniques must use T#### or T####.### format.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("MITRE techniques must not contain duplicates.")
        return normalized

    @field_validator("source_record_fingerprint")
    @classmethod
    def validate_defensive_sample_fingerprint(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("source_record_fingerprint must be a SHA-256 hexadecimal digest.")
        return normalized

    @field_validator("feature_payload")
    @classmethod
    def validate_defensive_sample_features(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value or len(value) > 64:
            raise ValueError("feature_payload must contain between 1 and 64 sanitized fields.")
        primitive = (str, int, float, bool)
        for key, feature in value.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,127}", key):
                raise ValueError("feature_payload keys must be bounded canonical names.")
            if not isinstance(feature, primitive):
                raise ValueError("feature_payload may contain sanitized scalar values only.")
            if isinstance(feature, str) and len(feature) > 512:
                raise ValueError("string feature values are limited to 512 characters.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_defensive_sample_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("defensive dataset samples cannot enable enforcement.")
        return value

    @model_validator(mode="after")
    def validate_defensive_sample_label(self) -> "DefensiveDatasetSample":
        if not self.sanitized:
            raise ValueError("defensive dataset samples must be sanitized.")
        if self.label == "benign" and (self.attack_family is not None or self.mitre_techniques):
            raise ValueError("benign samples cannot claim an attack family or MITRE technique.")
        if self.label == "attack" and not self.mitre_techniques:
            raise ValueError("attack samples require at least one MITRE technique.")
        return self


class DefensiveEvaluationPolicy(BaseModel):
    """Tenant-owned acceptance thresholds for advisory defensive model evaluation."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    name: str = Field(min_length=3, max_length=160)
    enabled: bool = True
    minimum_precision: float = Field(default=0.80, ge=0.50, le=1.0)
    minimum_recall: float = Field(default=0.80, ge=0.50, le=1.0)
    maximum_false_positive_rate: float = Field(default=0.10, ge=0.0, le=0.50)
    minimum_attack_samples: int = Field(default=5, ge=1, le=1_000_000)
    minimum_benign_samples: int = Field(default=5, ge=1, le=1_000_000)
    require_test_split: bool = True
    advisory_only: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_defensive_evaluation_policy_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("advisory_only")
    @classmethod
    def require_defensive_evaluation_advisory_only(cls, value: bool) -> bool:
        if not value:
            raise ValueError("defensive evaluation policies must remain advisory only.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_defensive_evaluation_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("defensive evaluation policies cannot enable enforcement.")
        return value


class DefensiveModelEvaluation(BaseModel):
    """Immutable evaluation result for an advisory scorer or model against a labelled corpus."""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    evaluation_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    policy_id: str
    dataset_id: str
    dataset_version: str
    dataset_fingerprint: str = Field(min_length=64, max_length=64)
    model_id: str = Field(min_length=3, max_length=160)
    model_version: str = Field(min_length=1, max_length=80)
    evaluated_split: Literal["validation", "test"]
    true_positive: int = Field(ge=0)
    false_positive: int = Field(ge=0)
    true_negative: int = Field(ge=0)
    false_negative: int = Field(ge=0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    false_positive_rate: float = Field(ge=0.0, le=1.0)
    status: Literal["accepted", "rejected", "insufficient_data"]
    rejection_reasons: List[str] = Field(default_factory=list, max_length=12)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    advisory_only: bool = True
    requires_human_approval: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_defensive_evaluation_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("dataset_version")
    @classmethod
    def validate_defensive_evaluation_dataset_version(cls, value: str) -> str:
        if not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value):
            raise ValueError("dataset_version must be a dotted numeric version.")
        return value

    @field_validator("dataset_fingerprint")
    @classmethod
    def validate_defensive_evaluation_fingerprint(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("dataset_fingerprint must be a SHA-256 hexadecimal digest.")
        return normalized

    @field_validator("evaluated_at")
    @classmethod
    def normalize_defensive_evaluation_timestamp(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @field_validator("advisory_only", "requires_human_approval")
    @classmethod
    def require_defensive_evaluation_human_controls(cls, value: bool) -> bool:
        if not value:
            raise ValueError("defensive model evaluations must remain advisory and approval-bound.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_defensive_model_evaluation_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("defensive model evaluations cannot enable enforcement.")
        return value

    @model_validator(mode="after")
    def validate_defensive_evaluation_metrics(self) -> "DefensiveModelEvaluation":
        predicted_positive = self.true_positive + self.false_positive
        actual_positive = self.true_positive + self.false_negative
        actual_negative = self.true_negative + self.false_positive
        expected_precision = self.true_positive / predicted_positive if predicted_positive else 0.0
        expected_recall = self.true_positive / actual_positive if actual_positive else 0.0
        expected_fpr = self.false_positive / actual_negative if actual_negative else 0.0
        for provided, expected, name in (
            (self.precision, expected_precision, "precision"),
            (self.recall, expected_recall, "recall"),
            (self.false_positive_rate, expected_fpr, "false_positive_rate"),
        ):
            if abs(provided - expected) > 0.000001:
                raise ValueError(f"{name} must match its confusion-matrix value.")
        if self.status == "accepted" and self.rejection_reasons:
            raise ValueError("accepted evaluations cannot contain rejection_reasons.")
        if self.status != "accepted" and not self.rejection_reasons:
            raise ValueError("rejected or insufficient-data evaluations require rejection_reasons.")
        return self


class AdvisoryModelAssessment(BaseModel):
    """Structured advisory model output; it can recommend investigation only and has no response authority."""

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    detection_id: str
    model_id: str = Field(min_length=3, max_length=160)
    model_version: str = Field(min_length=1, max_length=80)
    evaluation_id: Optional[str] = None
    classification: Literal["likely_benign", "suspicious", "insufficient_evidence"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: List[str] = Field(default_factory=list, max_length=16)
    reasons: List[str] = Field(min_length=1, max_length=12)
    recommended_mode: Literal["observe", "investigate"]
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    advisory_only: bool = True
    requires_human_approval: bool = True
    automatic_enforcement: bool = False

    @field_validator("tenant_id")
    @classmethod
    def validate_advisory_assessment_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("assessed_at")
    @classmethod
    def normalize_advisory_assessment_time(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @field_validator("advisory_only", "requires_human_approval")
    @classmethod
    def require_advisory_assessment_controls(cls, value: bool) -> bool:
        if not value:
            raise ValueError("advisory model assessments must remain approval-bound and advisory only.")
        return value

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_advisory_assessment_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("advisory model assessments cannot enable enforcement.")
        return value

    @model_validator(mode="after")
    def validate_advisory_assessment_evidence(self) -> "AdvisoryModelAssessment":
        if self.classification in {"suspicious", "likely_benign"} and not self.evidence_ids:
            raise ValueError("non-refusal advisory assessments require source evidence IDs.")
        if self.classification == "insufficient_evidence" and self.recommended_mode != "observe":
            raise ValueError("insufficient evidence assessments may only recommend observation.")
        return self


class TelemetryReplicationTarget(BaseModel):
    """A tenant-owned telemetry replication destination; it cannot transport response or audit commands."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    target_region: str = Field(min_length=2, max_length=64)
    stream_name: str = Field(min_length=3, max_length=255)
    enabled: bool = True
    telemetry_only: bool = True

    @field_validator("telemetry_only")
    @classmethod
    def require_telemetry_only_replication(cls, value: bool) -> bool:
        if not value:
            raise ValueError("replication targets must remain telemetry-only.")
        return value

    @field_validator("tenant_id")
    @classmethod
    def validate_replication_target_tenant(cls, value: str) -> str:
        try:
            from uuid import UUID
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc


class TelemetryReplicationReceipt(BaseModel):
    """Append-only receipt for one telemetry envelope delivery to one regional target."""

    model_config = ConfigDict(extra="forbid")

    receipt_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    target_id: str
    event_id: str
    source_region: str = Field(min_length=2, max_length=64)
    target_region: str = Field(min_length=2, max_length=64)
    payload_hash: str = Field(min_length=64, max_length=64)
    status: Literal["pending", "delivered", "failed"] = "pending"
    attempt_count: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivered_at: Optional[datetime] = None
    error_code: Optional[str] = None
    automatic_enforcement: bool = False

    @field_validator("automatic_enforcement")
    @classmethod
    def reject_replication_automatic_enforcement(cls, value: bool) -> bool:
        if value:
            raise ValueError("telemetry replication cannot enable automatic enforcement.")
        return value

    @field_validator("payload_hash")
    @classmethod
    def validate_replication_hash(cls, value: str) -> str:
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ValueError("payload_hash must be a lowercase SHA-256 hexadecimal digest.")
        return value

    @field_validator("created_at", "delivered_at")
    @classmethod
    def validate_replication_timestamps(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
