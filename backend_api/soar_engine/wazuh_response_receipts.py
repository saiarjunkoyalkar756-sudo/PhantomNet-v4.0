"""Durable signed endpoint receipts for the governed Wazuh Active Response bridge.

A Wazuh API acknowledgement only proves a command was sent. This service stores the separate,
HMAC-authenticated endpoint observation required to claim verified containment.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AsyncSessionLocal,
    ContainmentApprovalRow,
    ContainmentRequestRow,
    WazuhResponseReceiptRow,
    engine,
)


SessionFactory = Callable[[], AsyncSession]
_SHA256_HEX = re.compile(r"^[a-f0-9]{64}$")
_AGENT_ID = re.compile(r"^\d{3,16}$")


class WazuhResponseReceipt(BaseModel):
    """Exact post-action evidence emitted by an allow-listed endpoint response script."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str = Field(min_length=16, max_length=128)
    tenant_id: str
    request_id: str = Field(min_length=16, max_length=128)
    approval_id: str = Field(min_length=16, max_length=128)
    asset_id: str = Field(min_length=3, max_length=128)
    wazuh_agent_id: str = Field(min_length=3, max_length=16)
    action: Literal["isolate_endpoint", "release_endpoint"]
    network_state: Literal["isolated", "released"]
    command_fingerprint: str = Field(min_length=64, max_length=64)
    nonce: str = Field(min_length=16, max_length=256)
    observed_at: datetime
    signature_key_id: str = Field(min_length=3, max_length=128)
    signature: str = Field(min_length=64, max_length=64)

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, value: str) -> str:
        try:
            return str(UUID(value))
        except ValueError as exc:
            raise ValueError("tenant_id must be a UUID.") from exc

    @field_validator("wazuh_agent_id")
    @classmethod
    def validate_wazuh_agent_id(cls, value: str) -> str:
        if not _AGENT_ID.fullmatch(value):
            raise ValueError("wazuh_agent_id must be a numeric Wazuh agent identifier.")
        return value

    @field_validator("command_fingerprint", "signature")
    @classmethod
    def validate_sha256_hex(cls, value: str) -> str:
        normalized = value.lower()
        if not _SHA256_HEX.fullmatch(normalized):
            raise ValueError("value must be a lowercase SHA-256 hexadecimal digest.")
        return normalized

    @field_validator("observed_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def unsigned_payload(self) -> dict[str, str]:
        payload = self.model_dump(mode="json", exclude={"signature"})
        return {key: str(value) for key, value in payload.items()}


@dataclass(frozen=True)
class WazuhReceiptConfig:
    hmac_key: str | None
    key_id: str | None
    max_age_seconds: int = 300
    max_future_seconds: int = 30
    configuration_error: str | None = None

    @classmethod
    def from_environment(cls) -> "WazuhReceiptConfig":
        try:
            max_age = int(os.getenv("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_MAX_AGE_SECONDS", "300"))
            max_future = int(os.getenv("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_MAX_FUTURE_SECONDS", "30"))
            if not 1 <= max_age <= 900:
                raise ValueError("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_MAX_AGE_SECONDS must be between 1 and 900.")
            if not 0 <= max_future <= 120:
                raise ValueError("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_MAX_FUTURE_SECONDS must be between 0 and 120.")
            return cls(
                hmac_key=os.getenv("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY"),
                key_id=os.getenv("PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY_ID"),
                max_age_seconds=max_age,
                max_future_seconds=max_future,
            )
        except ValueError as exc:
            return cls(hmac_key=None, key_id=None, configuration_error=str(exc))


async def init_wazuh_response_receipt_store() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(WazuhResponseReceiptRow.__table__.create, checkfirst=True)


class WazuhResponseReceiptService:
    """Accept and retrieve HMAC-authenticated endpoint receipts; never authorizes execution."""

    def __init__(
        self,
        *,
        session_factory: SessionFactory = AsyncSessionLocal,
        config: WazuhReceiptConfig | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._config = config or WazuhReceiptConfig.from_environment()
        self._now = now or (lambda: datetime.now(timezone.utc))

    def _require_configuration(self) -> None:
        if self._config.configuration_error:
            raise PermissionError(f"Invalid Wazuh response receipt configuration: {self._config.configuration_error}")
        if not self._config.hmac_key or not self._config.key_id:
            raise PermissionError("Signed Wazuh response receipt verification is not configured.")

    @staticmethod
    def _canonical_payload(receipt: WazuhResponseReceipt) -> bytes:
        return json.dumps(receipt.unsigned_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _verify_signature_and_time(self, receipt: WazuhResponseReceipt) -> None:
        self._require_configuration()
        assert self._config.hmac_key is not None and self._config.key_id is not None
        if receipt.signature_key_id != self._config.key_id:
            raise PermissionError("Wazuh response receipt uses an unknown signature key identifier.")
        expected = hmac.new(self._config.hmac_key.encode("utf-8"), self._canonical_payload(receipt), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, receipt.signature):
            raise PermissionError("Wazuh response receipt signature is invalid.")
        now = self._now().astimezone(timezone.utc)
        if receipt.observed_at < now - timedelta(seconds=self._config.max_age_seconds):
            raise PermissionError("Wazuh response receipt is stale.")
        if receipt.observed_at > now + timedelta(seconds=self._config.max_future_seconds):
            raise PermissionError("Wazuh response receipt timestamp is in the future.")

    async def submit(self, receipt: WazuhResponseReceipt) -> WazuhResponseReceiptRow:
        """Persist one valid receipt after validating its cryptographic and lifecycle bindings."""
        self._verify_signature_and_time(receipt)
        received_at = self._now().astimezone(timezone.utc)
        async with self._session_factory() as session:
            request = await session.scalar(
                select(ContainmentRequestRow).where(
                    ContainmentRequestRow.tenant_id == UUID(receipt.tenant_id),
                    ContainmentRequestRow.request_id == receipt.request_id,
                )
            )
            approval = await session.scalar(
                select(ContainmentApprovalRow).where(
                    ContainmentApprovalRow.tenant_id == UUID(receipt.tenant_id),
                    ContainmentApprovalRow.request_id == receipt.request_id,
                    ContainmentApprovalRow.approval_id == receipt.approval_id,
                )
            )
            if request is None or approval is None or approval.decision != "approved":
                raise PermissionError("Wazuh response receipt is not bound to an approved containment request.")
            if request.asset_id != receipt.asset_id or receipt.asset_id != receipt.wazuh_agent_id:
                raise PermissionError("Wazuh response receipt asset binding does not match the approved request.")
            existing = await session.scalar(
                select(WazuhResponseReceiptRow).where(
                    (WazuhResponseReceiptRow.receipt_id == receipt.receipt_id)
                    | ((WazuhResponseReceiptRow.tenant_id == UUID(receipt.tenant_id)) & (WazuhResponseReceiptRow.nonce == receipt.nonce))
                )
            )
            if existing is not None:
                raise PermissionError("Wazuh response receipt was already accepted; replay is forbidden.")
            row = WazuhResponseReceiptRow(
                receipt_id=receipt.receipt_id,
                tenant_id=UUID(receipt.tenant_id),
                request_id=receipt.request_id,
                approval_id=receipt.approval_id,
                asset_id=receipt.asset_id,
                wazuh_agent_id=receipt.wazuh_agent_id,
                action=receipt.action,
                network_state=receipt.network_state,
                command_fingerprint=receipt.command_fingerprint,
                nonce=receipt.nonce,
                observed_at=receipt.observed_at,
                received_at=received_at,
                signature=receipt.signature,
                signature_key_id=receipt.signature_key_id,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise PermissionError("Wazuh response receipt conflicts with an existing receipt and was rejected.") from exc
            await session.refresh(row)
            return row

    async def find_verified_receipt(
        self,
        *,
        tenant_id: str,
        request_id: str,
        approval_id: str,
        asset_id: str,
        action: Literal["isolate_endpoint", "release_endpoint"],
        expected_network_state: Literal["isolated", "released"],
        command_fingerprint: str,
        not_before: datetime,
    ) -> WazuhResponseReceiptRow | None:
        """Return only a fresh exact receipt received after the Wazuh dispatch attempt."""
        self._require_configuration()
        cutoff = self._now().astimezone(timezone.utc) - timedelta(seconds=self._config.max_age_seconds)
        effective_not_before = max(not_before.astimezone(timezone.utc), cutoff)
        async with self._session_factory() as session:
            return await session.scalar(
                select(WazuhResponseReceiptRow)
                .where(
                    WazuhResponseReceiptRow.tenant_id == UUID(tenant_id),
                    WazuhResponseReceiptRow.request_id == request_id,
                    WazuhResponseReceiptRow.approval_id == approval_id,
                    WazuhResponseReceiptRow.asset_id == asset_id,
                    WazuhResponseReceiptRow.wazuh_agent_id == asset_id,
                    WazuhResponseReceiptRow.action == action,
                    WazuhResponseReceiptRow.network_state == expected_network_state,
                    WazuhResponseReceiptRow.command_fingerprint == command_fingerprint,
                    WazuhResponseReceiptRow.received_at >= effective_not_before,
                )
                .order_by(WazuhResponseReceiptRow.received_at.desc())
                .limit(1)
            )
