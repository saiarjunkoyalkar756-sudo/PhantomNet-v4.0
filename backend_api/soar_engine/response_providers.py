"""Controlled provider boundary for real SOAR response actions.

No provider is enabled by default.  A configured provider must receive an approved,
allowlisted test-lab request and return verifiable evidence before PhantomNet reports
enforcement as successful.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import time
from typing import Any, Callable, Dict, Protocol

import httpx

from backend_api.iam_service.policy import authorize


@dataclass(frozen=True)
class ResponseRequest:
    action: str
    target: str
    tenant_id: str
    requested_by: str
    approval_id: str | None
    idempotency_key: str
    metadata: Dict[str, Any]


class ResponseProvider(Protocol):
    def execute(self, request: ResponseRequest) -> Dict[str, Any]: ...


class DisabledResponseProvider:
    def execute(self, request: ResponseRequest) -> Dict[str, Any]:
        return {
            "status": "failure",
            "detail": "No external response provider is enabled; no action was executed.",
            "enforced": False,
            "verified": False,
            "provider": "disabled",
            "idempotency_key": request.idempotency_key,
        }


class HttpResponseProvider:
    """Generic provider client for an explicitly configured lab integration endpoint."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_token: str | None = None,
        allowed_tenants: set[str] | None = None,
        allowed_targets: set[str] | None = None,
        requester: Callable[..., httpx.Response] | None = None,
        max_attempts: int = 2,
    ) -> None:
        self.endpoint = endpoint or os.getenv("PHANTOMNET_RESPONSE_PROVIDER_URL", "")
        self.api_token = api_token if api_token is not None else os.getenv("PHANTOMNET_RESPONSE_PROVIDER_TOKEN", "")
        self.allowed_tenants = allowed_tenants or {
            tenant.strip() for tenant in os.getenv("PHANTOMNET_RESPONSE_ALLOWED_TENANTS", "").split(",") if tenant.strip()
        }
        self.allowed_targets = allowed_targets or {
            target.strip() for target in os.getenv("PHANTOMNET_RESPONSE_ALLOWED_TARGETS", "").split(",") if target.strip()
        }
        self.requester = requester or httpx.post
        self.max_attempts = max_attempts

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_token)

    def _reject(self, request: ResponseRequest, detail: str) -> Dict[str, Any]:
        return {
            "status": "failure",
            "detail": detail,
            "enforced": False,
            "verified": False,
            "provider": "http",
            "idempotency_key": request.idempotency_key,
        }

    def execute(self, request: ResponseRequest) -> Dict[str, Any]:
        if not self.is_configured():
            return self._reject(request, "External response provider is not configured.")
        if request.tenant_id not in self.allowed_tenants:
            return self._reject(request, "Tenant is not allowlisted for external response actions.")
        if request.target not in self.allowed_targets:
            return self._reject(request, "Target is not allowlisted for the configured test lab.")
        if not request.approval_id:
            return self._reject(request, "A recorded approval identifier is required for external response actions.")
        requester_role = str(request.metadata.get("requester_role", "viewer"))
        capability = "response:approve" if request.action in {"isolate_host", "terminate_process"} else "response:request"
        decision = authorize(requester_role, capability)
        if not decision.allowed:
            return self._reject(request, f"RBAC denied {capability} for role {requester_role}.")

        payload = {
            "action": request.action,
            "target": request.target,
            "tenant_id": request.tenant_id,
            "requested_by": request.requested_by,
            "approval_id": request.approval_id,
            "metadata": request.metadata,
        }
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Idempotency-Key": request.idempotency_key,
            "Content-Type": "application/json",
        }
        last_error = "provider did not return a response"
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.requester(self.endpoint, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                evidence = response.json()
                verified = bool(evidence.get("verified"))
                enforced = bool(evidence.get("enforced"))
                return {
                    "status": "success" if enforced and verified else "failure",
                    "detail": evidence.get("detail", "Provider response received."),
                    "enforced": enforced,
                    "verified": verified,
                    "provider": evidence.get("provider", "http"),
                    "provider_request_id": evidence.get("request_id"),
                    "idempotency_key": request.idempotency_key,
                    "attempts": attempt,
                }
            except (httpx.HTTPError, ValueError) as error:
                last_error = str(error)
                if attempt < self.max_attempts:
                    time.sleep(0.1 * attempt)
        return self._reject(request, f"Provider request failed after {self.max_attempts} attempts: {last_error}")


def get_response_provider() -> ResponseProvider:
    provider = HttpResponseProvider()
    return provider if provider.is_configured() else DisabledResponseProvider()
