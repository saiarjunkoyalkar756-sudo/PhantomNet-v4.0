"""Governed incident-response proposals derived from detections.

Policies can create a containment request only. The existing containment service still requires a
separate human approval, signed audit evidence, adapter execution, verification, and rollback.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import AsyncSessionLocal, ResponseAutomationPolicyRow, engine
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import ContainmentRequest, DetectionRecord, ResponseAutomationPolicy


SessionFactory = Callable[[], AsyncSession]
SEVERITY_ORDER = {"informational": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _policy_contract(row: ResponseAutomationPolicyRow) -> ResponseAutomationPolicy:
    return ResponseAutomationPolicy(
        policy_id=row.policy_id,
        tenant_id=str(row.tenant_id),
        name=row.name,
        enabled=row.enabled,
        trigger_rule_ids=list(row.trigger_rule_ids),
        minimum_severity=row.minimum_severity,
        action=row.action,
        target=row.target,
        asset_id=row.asset_id,
        parameters=dict(row.parameters),
        requires_approval=True,
        automatic_enforcement=False,
    )


async def init_response_automation_store() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(ResponseAutomationPolicyRow.__table__.create, checkfirst=True)


class ResponseAutomationPolicyRepository:
    """Tenant-owned policy persistence; policies have no execution fields."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    async def upsert(self, policy: ResponseAutomationPolicy) -> ResponseAutomationPolicy:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(ResponseAutomationPolicyRow).where(
                    ResponseAutomationPolicyRow.tenant_id == UUID(policy.tenant_id),
                    ResponseAutomationPolicyRow.name == policy.name,
                )
            )
            now = datetime.now(timezone.utc)
            if row is None:
                row = ResponseAutomationPolicyRow(
                    policy_id=policy.policy_id,
                    tenant_id=UUID(policy.tenant_id),
                    name=policy.name,
                    enabled=policy.enabled,
                    trigger_rule_ids=policy.trigger_rule_ids,
                    minimum_severity=policy.minimum_severity,
                    action=policy.action,
                    target=policy.target,
                    asset_id=policy.asset_id,
                    parameters=policy.parameters,
                    created_at=now,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.enabled = policy.enabled
                row.trigger_rule_ids = policy.trigger_rule_ids
                row.minimum_severity = policy.minimum_severity
                row.action = policy.action
                row.target = policy.target
                row.asset_id = policy.asset_id
                row.parameters = policy.parameters
                row.updated_at = now
            await session.commit()
            return _policy_contract(row)

    async def list_for_tenant(self, tenant_id: str, enabled_only: bool = False) -> list[ResponseAutomationPolicy]:
        async with self._session_factory() as session:
            statement = select(ResponseAutomationPolicyRow).where(ResponseAutomationPolicyRow.tenant_id == UUID(tenant_id))
            if enabled_only:
                statement = statement.where(ResponseAutomationPolicyRow.enabled.is_(True))
            rows = await session.scalars(statement.order_by(ResponseAutomationPolicyRow.name))
            return [_policy_contract(row) for row in rows]


class GovernedResponseProposalService:
    """Creates approval-required containment requests for matching policies and never executes a response."""

    def __init__(
        self,
        policies: ResponseAutomationPolicyRepository,
        containment: GovernedContainmentService,
    ) -> None:
        self._policies = policies
        self._containment = containment

    async def propose_for_detection(self, detection: DetectionRecord) -> list[ContainmentRequest]:
        """Return requests created from a detection; no policy can bypass the containment approval gate."""
        enabled_policies = await self._policies.list_for_tenant(detection.tenant_id, enabled_only=True)
        if not enabled_policies:
            return []
        self._containment.require_signed_audit_configuration()
        proposals: list[ContainmentRequest] = []
        for policy in enabled_policies:
            if policy.trigger_rule_ids and detection.rule_id not in policy.trigger_rule_ids:
                continue
            if SEVERITY_ORDER[detection.severity] < SEVERITY_ORDER[policy.minimum_severity]:
                continue
            idempotency_key = sha256(
                f"response-policy:{policy.policy_id}:detection:{detection.detection_id}".encode("utf-8")
            ).hexdigest()
            request = ContainmentRequest(
                tenant_id=detection.tenant_id,
                action=policy.action,
                target=policy.target,
                asset_id=policy.asset_id,
                playbook_id=None,
                requested_by=f"response-policy:{policy.policy_id}",
                idempotency_key=idempotency_key,
                parameters={
                    **policy.parameters,
                    "proposal_policy_id": policy.policy_id,
                    "source_detection_id": detection.detection_id,
                    "source_rule_id": detection.rule_id,
                },
                requires_approval=True,
                automatic_enforcement=False,
            )
            stored, _ = await self._containment.request(request)
            proposals.append(stored)
        return proposals


class ResponseProposalObserver:
    """Best-effort proposal observer that fails closed and visibly when audit configuration is absent."""

    def __init__(self, proposals: GovernedResponseProposalService) -> None:
        self._proposals = proposals

    async def observe(self, detection: DetectionRecord) -> list[ContainmentRequest]:
        try:
            return await self._proposals.propose_for_detection(detection)
        except PermissionError:
            # The policy cannot create a high-impact request without the same signed-audit
            # configuration needed for execution. Canonical detection remains durable.
            from loguru import logger
            logger.error(
                "Response policy proposal skipped because containment audit configuration is not ready.",
                tenant_id=detection.tenant_id,
                detection_id=detection.detection_id,
            )
            return []
