"""Scoped endpoint containment adapter; disabled by default and never self-approving."""

from __future__ import annotations

import os
from typing import Any, Callable

from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


class EndpointContainmentAdapter:
    """Dispatch approved endpoint commands only to explicitly allowlisted test-lab assets."""

    name = "endpoint-command"

    def __init__(
        self,
        enabled: bool | None = None,
        allowed_tenants: set[str] | None = None,
        allowed_assets: set[str] | None = None,
        dispatcher: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.enabled = enabled if enabled is not None else os.getenv("PHANTOMNET_ENDPOINT_CONTAINMENT_ENABLED", "false").lower() == "true"
        self.allowed_tenants = allowed_tenants or {
            value.strip() for value in os.getenv("PHANTOMNET_ENDPOINT_CONTAINMENT_ALLOWED_TENANTS", "").split(",") if value.strip()
        }
        self.allowed_assets = allowed_assets or {
            value.strip() for value in os.getenv("PHANTOMNET_ENDPOINT_CONTAINMENT_ALLOWED_ASSETS", "").split(",") if value.strip()
        }
        self.dispatcher = dispatcher

    def _reject(self, detail: str) -> dict[str, Any]:
        return {"enforced": False, "verified": False, "rollback_available": False, "detail": detail, "provider": self.name}

    def _allowed(self, request: ContainmentRequest) -> str | None:
        if not self.enabled:
            return "Endpoint containment adapter is disabled by default."
        if request.tenant_id not in self.allowed_tenants:
            return "Tenant is not allowlisted for endpoint containment."
        if not request.asset_id or request.asset_id not in self.allowed_assets:
            return "Endpoint asset is not allowlisted for containment."
        if request.action not in {"isolate_endpoint", "release_endpoint", "remediate_configuration"}:
            return f"Unsupported endpoint containment action: {request.action}."
        if self.dispatcher is None:
            return "No endpoint command dispatcher is configured."
        return None

    def preflight(self, request: ContainmentRequest) -> dict[str, Any]:
        """Evaluate local configuration and exact allowlist scope without dispatching an endpoint command."""
        denial = self._allowed(request)
        return {
            "eligible": denial is None,
            "provider": self.name,
            "detail": denial or "Endpoint containment scope and dispatcher are configured for the requested action.",
            "rollback_available": request.action == "isolate_endpoint" and denial is None,
            "verification_mode": "dispatcher_evidence_required",
            "external_calls": False,
            "automatic_enforcement": False,
        }

    def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        denial = self._allowed(request)
        if denial:
            return self._reject(denial)
        command = {
            "command_type": {
                "isolate_endpoint": "network_isolate",
                "release_endpoint": "network_release",
                "remediate_configuration": "remediate_configuration",
            }[request.action],
            "tenant_id": request.tenant_id,
            "target_agent_id": request.asset_id,
            "target": request.target,
            "approval_id": approval.approval_id,
            "idempotency_key": request.idempotency_key,
            "parameters": request.parameters,
        }
        result = self.dispatcher(command)
        return {
            "enforced": bool(result.get("enforced")),
            "verified": bool(result.get("verified")),
            "rollback_available": bool(result.get("rollback_available", request.action == "isolate_endpoint")),
            "detail": result.get("detail", "Endpoint command dispatcher returned no detail."),
            "command_id": result.get("command_id"),
            "provider": self.name,
        }

    def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        if request.action != "isolate_endpoint":
            return self._reject("Only a verified endpoint isolation request can be rolled back by this adapter.")
        rollback_request = request.model_copy(update={"action": "release_endpoint"})
        result = self.execute(rollback_request, approval)
        result["rollback_of"] = request.request_id
        return result
