"""Canonical contracts shared across PhantomNet telemetry, detection, and analyst workflows."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


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
