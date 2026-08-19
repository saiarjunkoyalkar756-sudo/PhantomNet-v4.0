"""Fail-closed Wazuh Active Response adapter for governed containment.

The Wazuh API can acknowledge command delivery but cannot prove an endpoint's final network
state. This adapter therefore treats Wazuh acknowledgement as dispatch evidence only and
requires a separate, signed endpoint receipt before it reports verified containment.
"""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import ipaddress
import json
import os
import re
from typing import Any, Awaitable, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from backend_api.soar_engine.wazuh_response_receipts import WazuhResponseReceiptService
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


_AGENT_ID = re.compile(r"^\d{3,16}$")
_PROFILE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


class WazuhResponseSpec(BaseModel):
    """Bounded, operator-reviewed parameters for one Wazuh endpoint response."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    wazuh_agent_id: str = Field(min_length=3, max_length=16)
    response_profile: str = Field(min_length=3, max_length=64)
    management_cidr: str
    verification_timeout_seconds: int = Field(default=30, ge=1, le=90)

    @field_validator("wazuh_agent_id")
    @classmethod
    def validate_agent_id(cls, value: str) -> str:
        if not _AGENT_ID.fullmatch(value):
            raise ValueError("wazuh_agent_id must be a numeric Wazuh agent identifier.")
        return value

    @field_validator("response_profile")
    @classmethod
    def validate_profile(cls, value: str) -> str:
        if not _PROFILE.fullmatch(value):
            raise ValueError("response_profile must be a bounded lowercase deployment profile name.")
        return value

    @field_validator("management_cidr")
    @classmethod
    def validate_management_cidr(cls, value: str) -> str:
        network = ipaddress.ip_network(value, strict=False)
        if network.version != 4:
            raise ValueError("management_cidr must be an IPv4 CIDR.")
        return str(network)


@dataclass(frozen=True)
class WazuhActiveResponseConfig:
    enabled: bool
    api_base_url: str
    username: str | None
    password: str | None
    command_hmac_key: str | None
    command_hmac_key_id: str | None
    tenant_agent_allowlist: dict[str, frozenset[str]]
    allowed_profiles: frozenset[str]
    request_timeout_seconds: int = 10
    receipt_poll_interval_seconds: float = 0.5
    allow_insecure_http: bool = False
    configuration_error: str | None = None

    @classmethod
    def from_environment(cls) -> "WazuhActiveResponseConfig":
        try:
            allowlist_raw = json.loads(os.getenv("PHANTOMNET_WAZUH_RESPONSE_TENANT_AGENT_ALLOWLIST", "{}"))
            if not isinstance(allowlist_raw, dict):
                raise ValueError("PHANTOMNET_WAZUH_RESPONSE_TENANT_AGENT_ALLOWLIST must be a JSON object.")
            mapping: dict[str, frozenset[str]] = {}
            for tenant_id, agent_ids in allowlist_raw.items():
                if not isinstance(tenant_id, str) or not isinstance(agent_ids, list) or not all(isinstance(agent_id, str) and _AGENT_ID.fullmatch(agent_id) for agent_id in agent_ids):
                    raise ValueError("Wazuh tenant-agent allowlist must map tenant IDs to numeric agent-ID arrays.")
                mapping[tenant_id] = frozenset(agent_ids)
            profiles = frozenset(value.strip() for value in os.getenv("PHANTOMNET_WAZUH_RESPONSE_ALLOWED_PROFILES", "").split(",") if value.strip())
            if any(not _PROFILE.fullmatch(profile) for profile in profiles):
                raise ValueError("PHANTOMNET_WAZUH_RESPONSE_ALLOWED_PROFILES contains an invalid profile name.")
            request_timeout = int(os.getenv("PHANTOMNET_WAZUH_RESPONSE_REQUEST_TIMEOUT_SECONDS", "10"))
            if not 1 <= request_timeout <= 30:
                raise ValueError("PHANTOMNET_WAZUH_RESPONSE_REQUEST_TIMEOUT_SECONDS must be between 1 and 30.")
            poll_interval = float(os.getenv("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_POLL_INTERVAL_SECONDS", "0.5"))
            if not 0.1 <= poll_interval <= 5:
                raise ValueError("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_POLL_INTERVAL_SECONDS must be between 0.1 and 5.")
            config = cls(
                enabled=os.getenv("PHANTOMNET_WAZUH_RESPONSE_ENABLED", "false").strip().lower() == "true",
                api_base_url=os.getenv("PHANTOMNET_WAZUH_RESPONSE_API_BASE_URL", "").rstrip("/"),
                username=os.getenv("PHANTOMNET_WAZUH_RESPONSE_API_USERNAME"),
                password=os.getenv("PHANTOMNET_WAZUH_RESPONSE_API_PASSWORD"),
                command_hmac_key=os.getenv("PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY"),
                command_hmac_key_id=os.getenv("PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY_ID"),
                tenant_agent_allowlist=mapping,
                allowed_profiles=profiles,
                request_timeout_seconds=request_timeout,
                receipt_poll_interval_seconds=poll_interval,
                allow_insecure_http=os.getenv("PHANTOMNET_WAZUH_RESPONSE_ALLOW_INSECURE_HTTP", "false").strip().lower() == "true",
            )
            config.validate()
            return config
        except (ValueError, json.JSONDecodeError) as exc:
            return cls(
                enabled=False,
                api_base_url="",
                username=None,
                password=None,
                command_hmac_key=None,
                command_hmac_key_id=None,
                tenant_agent_allowlist={},
                allowed_profiles=frozenset(),
                configuration_error=f"Invalid Wazuh Active Response configuration: {exc}",
            )

    def validate(self) -> None:
        parsed = urlparse(self.api_base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("PHANTOMNET_WAZUH_RESPONSE_API_BASE_URL must be an absolute HTTP(S) URL.")
        if parsed.scheme not in {"https", "http"}:
            raise ValueError("Wazuh API base URL must use HTTP(S).")
        if parsed.scheme != "https" and not self.allow_insecure_http:
            raise ValueError("Wazuh Active Response requires HTTPS unless explicitly enabled for an isolated lab.")
        if not self.username or not self.password:
            raise ValueError("Wazuh Active Response requires environment-managed API credentials.")
        if not self.command_hmac_key or not self.command_hmac_key_id:
            raise ValueError("Wazuh Active Response requires an environment-managed command HMAC key and key identifier.")
        if not self.tenant_agent_allowlist or not self.allowed_profiles:
            raise ValueError("Wazuh Active Response requires non-empty tenant-agent and profile allowlists.")


class WazuhActiveResponseClient(Protocol):
    """Mockable Wazuh transport: it must only send a named response to one agent."""

    def dispatch(self, *, agent_id: str, command: str, arguments: list[str], alert: dict[str, Any]) -> dict[str, Any]: ...


class HttpWazuhActiveResponseClient:
    """Minimal Wazuh REST client that obtains a short-lived token for each dispatch attempt."""

    def __init__(self, config: WazuhActiveResponseConfig, opener: Callable[..., Any] | None = None):
        self._config = config
        self._opener = opener or urlopen

    def _request_json(self, request: Request) -> dict[str, Any]:
        try:
            with self._opener(request, timeout=self._config.request_timeout_seconds) as response:
                raw = response.read(1_048_576)
                if response.status != 200:
                    raise RuntimeError(f"Wazuh API returned HTTP {response.status}.")
        except HTTPError as exc:
            raise RuntimeError(f"Wazuh API returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Wazuh API is unavailable.") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Wazuh API returned malformed JSON.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Wazuh API returned an invalid response shape.")
        return payload

    def _token(self) -> str:
        assert self._config.username and self._config.password
        credentials = base64.b64encode(f"{self._config.username}:{self._config.password}".encode("utf-8")).decode("ascii")
        request = Request(
            f"{self._config.api_base_url}/security/user/authenticate",
            headers={"Authorization": f"Basic {credentials}", "Accept": "application/json"},
            method="POST",
        )
        payload = self._request_json(request)
        token = payload.get("data", {}).get("token") if isinstance(payload.get("data"), dict) else None
        if not isinstance(token, str) or not token:
            raise RuntimeError("Wazuh API authentication did not return a JWT.")
        return token

    def dispatch(self, *, agent_id: str, command: str, arguments: list[str], alert: dict[str, Any]) -> dict[str, Any]:
        token = self._token()
        query = urlencode({"agents_list": agent_id, "wait_for_complete": "true"})
        body = json.dumps({"command": command, "arguments": arguments, "alert": alert}, separators=(",", ":")).encode("utf-8")
        request = Request(
            f"{self._config.api_base_url}/active-response?{query}",
            data=body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
            method="PUT",
        )
        payload = self._request_json(request)
        if payload.get("error") not in {0, "0"}:
            raise RuntimeError("Wazuh API reported an Active Response error.")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RuntimeError("Wazuh API Active Response acknowledgement has no data object.")
        affected = [str(value) for value in data.get("affected_items", [])]
        failed = int(data.get("total_failed_items", 0))
        if failed != 0 or affected != [agent_id]:
            raise RuntimeError("Wazuh API did not acknowledge exactly the one approved target agent.")
        return {
            "accepted": True,
            "wazuh_agent_id": agent_id,
            "affected_items": affected,
            "total_failed_items": failed,
            "message": str(payload.get("message", "Wazuh command sent.")),
        }


class WazuhActiveResponseContainmentAdapter:
    """Dispatch one approved named Wazuh command, then require a matching signed endpoint receipt."""

    name = "wazuh-active-response"

    def __init__(
        self,
        *,
        config: WazuhActiveResponseConfig | None = None,
        client: WazuhActiveResponseClient | None = None,
        receipt_service: WazuhResponseReceiptService | None = None,
        now: Callable[[], datetime] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self._config = config or WazuhActiveResponseConfig.from_environment()
        self._client = client or HttpWazuhActiveResponseClient(self._config)
        self._receipt_service = receipt_service or WazuhResponseReceiptService()
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._sleep = sleep or asyncio.sleep

    def _reject(self, detail: str, *, spec: WazuhResponseSpec | None = None, dispatch: dict[str, Any] | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "enforced": False,
            "verified": False,
            "rollback_available": False,
            "detail": detail,
            "provider": self.name,
        }
        if spec is not None:
            result["wazuh"] = {"agent_id": spec.wazuh_agent_id, "response_profile": spec.response_profile, "management_cidr": spec.management_cidr}
        if dispatch is not None:
            result["dispatch"] = dispatch
        return result

    def _parse_and_authorize(self, request: ContainmentRequest, approval: ContainmentApproval) -> tuple[WazuhResponseSpec | None, str | None]:
        if not self._config.enabled:
            return None, "Wazuh Active Response containment adapter is disabled by default."
        if self._config.configuration_error:
            return None, self._config.configuration_error
        try:
            self._config.validate()
        except ValueError as exc:
            return None, f"Invalid Wazuh Active Response configuration: {exc}"
        if request.action not in {"isolate_endpoint", "release_endpoint"}:
            return None, f"Unsupported Wazuh Active Response action: {request.action}."
        if not request.requires_approval or request.automatic_enforcement or approval.decision != "approved":
            return None, "Wazuh Active Response requires an explicitly approved, non-automatic request."
        try:
            spec = WazuhResponseSpec.model_validate(request.parameters)
        except ValidationError as exc:
            return None, f"Invalid Wazuh Active Response parameters: {exc.errors()[0]['msg']}"
        if request.asset_id != spec.wazuh_agent_id or request.target != spec.wazuh_agent_id:
            return None, "Containment target and asset_id must both exactly equal the approved Wazuh agent ID."
        if spec.wazuh_agent_id not in self._config.tenant_agent_allowlist.get(request.tenant_id, frozenset()):
            return None, "Tenant is not allowlisted for the requested Wazuh agent."
        if spec.response_profile not in self._config.allowed_profiles:
            return None, "Wazuh response profile is not allowlisted."
        return spec, None

    @staticmethod
    def _command_for(action: Literal["isolate_endpoint", "release_endpoint"]) -> str:
        return "!phantomnet-network-isolate" if action == "isolate_endpoint" else "!phantomnet-network-release"

    @staticmethod
    def _expected_state(action: Literal["isolate_endpoint", "release_endpoint"]) -> Literal["isolated", "released"]:
        return "isolated" if action == "isolate_endpoint" else "released"

    @staticmethod
    def _fingerprint(request: ContainmentRequest, approval: ContainmentApproval, spec: WazuhResponseSpec) -> str:
        bound = {
            "action": request.action,
            "approval_id": approval.approval_id,
            "asset_id": request.asset_id,
            "management_cidr": spec.management_cidr,
            "request_id": request.request_id,
            "response_profile": spec.response_profile,
            "tenant_id": request.tenant_id,
            "wazuh_agent_id": spec.wazuh_agent_id,
        }
        return sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _command_signature(self, fingerprint: str) -> str:
        assert self._config.command_hmac_key is not None
        return hmac.new(self._config.command_hmac_key.encode("utf-8"), fingerprint.encode("ascii"), sha256).hexdigest()

    async def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        spec, denial = self._parse_and_authorize(request, approval)
        if denial:
            return self._reject(denial, spec=spec)
        assert spec is not None
        action: Literal["isolate_endpoint", "release_endpoint"] = request.action  # type: ignore[assignment]
        fingerprint = self._fingerprint(request, approval, spec)
        dispatch_started_at = self._now().astimezone(timezone.utc)
        command = self._command_for(action)
        assert self._config.command_hmac_key_id is not None
        arguments = [
            request.tenant_id,
            request.request_id,
            approval.approval_id,
            spec.wazuh_agent_id,
            spec.response_profile,
            spec.management_cidr,
            fingerprint,
            self._config.command_hmac_key_id,
            self._command_signature(fingerprint),
        ]
        alert = {"data": {"phantomnet": {"tenant_id": request.tenant_id, "request_id": request.request_id, "approval_id": approval.approval_id, "asset_id": spec.wazuh_agent_id, "action": action, "command_fingerprint": fingerprint}}}
        try:
            dispatch = self._client.dispatch(agent_id=spec.wazuh_agent_id, command=command, arguments=arguments, alert=alert)
        except Exception as exc:
            return self._reject(f"Wazuh Active Response dispatch failed without verified enforcement: {type(exc).__name__}", spec=spec)
        if not dispatch.get("accepted"):
            return self._reject("Wazuh Active Response did not acknowledge command dispatch.", spec=spec, dispatch=dispatch)
        expected_state = self._expected_state(action)
        deadline = self._now().astimezone(timezone.utc).timestamp() + spec.verification_timeout_seconds
        while self._now().astimezone(timezone.utc).timestamp() <= deadline:
            try:
                receipt = await self._receipt_service.find_verified_receipt(
                    tenant_id=request.tenant_id,
                    request_id=request.request_id,
                    approval_id=approval.approval_id,
                    asset_id=spec.wazuh_agent_id,
                    action=action,
                    expected_network_state=expected_state,
                    command_fingerprint=fingerprint,
                    not_before=dispatch_started_at,
                )
            except Exception as exc:
                return self._reject(f"Wazuh endpoint receipt verification failed closed: {type(exc).__name__}", spec=spec, dispatch=dispatch)
            if receipt is not None:
                return {
                    "enforced": True,
                    "verified": True,
                    "rollback_available": action == "isolate_endpoint",
                    "detail": "Wazuh command dispatch and a fresh exact signed endpoint receipt verified the approved network state.",
                    "provider": self.name,
                    "dispatch": dispatch,
                    "wazuh": {
                        "agent_id": spec.wazuh_agent_id,
                        "response_profile": spec.response_profile,
                        "management_cidr": spec.management_cidr,
                        "command": command,
                        "command_fingerprint": fingerprint,
                        "expected_network_state": expected_state,
                        "receipt_id": receipt.receipt_id,
                        "receipt_observed_at": receipt.observed_at.isoformat(),
                    },
                }
            await self._sleep(self._config.receipt_poll_interval_seconds)
        return self._reject("Wazuh command was acknowledged but no fresh matching signed endpoint receipt arrived before verification timeout.", spec=spec, dispatch=dispatch)

    async def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        if request.action != "isolate_endpoint":
            return self._reject("Only a verified Wazuh endpoint-isolation request can be rolled back.")
        release_request = request.model_copy(update={"action": "release_endpoint"})
        result = await self.execute(release_request, approval)
        result["rollback_of"] = request.request_id
        return result
