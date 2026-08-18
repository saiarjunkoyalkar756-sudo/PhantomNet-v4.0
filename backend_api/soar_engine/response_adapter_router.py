"""Deterministic routing for governed response adapters.

Routing is based solely on the already-approved canonical action. This class never approves,
creates, mutates, or executes a request on its own; it delegates to adapters that remain
individually fail-closed and evidence-producing.
"""

from __future__ import annotations

from typing import Any

from backend_api.soar_engine.aws_security_group_adapter import AwsSecurityGroupContainmentAdapter
from backend_api.soar_engine.endpoint_containment_adapter import EndpointContainmentAdapter
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


class GovernedResponseAdapterRouter:
    name = "governed-response-router"

    def __init__(
        self,
        *,
        endpoint_adapter: EndpointContainmentAdapter | None = None,
        aws_security_group_adapter: AwsSecurityGroupContainmentAdapter | None = None,
    ) -> None:
        self._endpoint_adapter = endpoint_adapter or EndpointContainmentAdapter()
        self._aws_security_group_adapter = aws_security_group_adapter or AwsSecurityGroupContainmentAdapter()

    def _adapter_for(self, request: ContainmentRequest):
        if request.action == "block_indicator":
            return self._aws_security_group_adapter
        return self._endpoint_adapter

    def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        return self._adapter_for(request).execute(request, approval)

    def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        return self._adapter_for(request).rollback(request, approval)
