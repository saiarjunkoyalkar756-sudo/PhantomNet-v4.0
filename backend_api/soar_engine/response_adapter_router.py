"""Deterministic routing for governed response adapters.

Routing is based solely on the already-approved canonical action. This class never approves,
creates, mutates, or executes a request on its own; it delegates to adapters that remain
individually fail-closed and evidence-producing.
"""

from __future__ import annotations

from typing import Any

from backend_api.soar_engine.aws_security_group_adapter import AwsSecurityGroupContainmentAdapter
from backend_api.soar_engine.endpoint_containment_adapter import EndpointContainmentAdapter
from backend_api.soar_engine.wazuh_active_response_adapter import WazuhActiveResponseContainmentAdapter
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


class GovernedResponseAdapterRouter:
    name = "governed-response-router"

    def __init__(
        self,
        *,
        endpoint_adapter: EndpointContainmentAdapter | None = None,
        aws_security_group_adapter: AwsSecurityGroupContainmentAdapter | None = None,
        wazuh_active_response_adapter: WazuhActiveResponseContainmentAdapter | None = None,
    ) -> None:
        self._endpoint_adapter = endpoint_adapter or EndpointContainmentAdapter()
        self._aws_security_group_adapter = aws_security_group_adapter or AwsSecurityGroupContainmentAdapter()
        self._wazuh_active_response_adapter = wazuh_active_response_adapter or WazuhActiveResponseContainmentAdapter()

    def _adapter_for(self, request: ContainmentRequest):
        if request.action == "block_indicator":
            return self._aws_security_group_adapter
        if request.action in {"isolate_endpoint", "release_endpoint"} and "wazuh_agent_id" in request.parameters:
            return self._wazuh_active_response_adapter
        return self._endpoint_adapter

    def preflight(self, request: ContainmentRequest) -> dict[str, Any]:
        """Return adapter-local eligibility only; this method never calls an external provider or dispatches an action."""
        adapter = self._adapter_for(request)
        method = getattr(adapter, "preflight", None)
        if not callable(method):
            return {
                "eligible": False,
                "provider": getattr(adapter, "name", "unknown"),
                "detail": "Selected containment adapter does not implement a side-effect-free preflight.",
                "rollback_available": False,
                "verification_mode": "unavailable",
                "external_calls": False,
                "automatic_enforcement": False,
            }
        return method(request)

    def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        return self._adapter_for(request).execute(request, approval)

    def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        return self._adapter_for(request).rollback(request, approval)
