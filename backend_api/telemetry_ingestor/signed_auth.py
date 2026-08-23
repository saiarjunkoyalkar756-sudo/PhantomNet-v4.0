"""Tenant-bound detached-signature verification for canonical telemetry ingestion.

The verifier authenticates telemetry only. It cannot create, approve, dispatch, or execute
any response action. Accepted nonces are durable and append-only so replay remains rejected
after a process restart.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.hazmat.primitives import serialization

from backend_api.shared.database import (
    AsyncSessionLocal,
    TelemetryAgentCredentialRow,
    TelemetrySignatureNonceRow,
)
from backend_api.shared.security_utils import verify_signature
from phantomnet_core.contracts import SignedTelemetryEnvelope, TelemetrySigningCredential


SessionFactory = Callable[[], AsyncSession]
TELEMETRY_SIGNATURE_DOMAIN = "phantomnet.telemetry.v1"


class SignedTelemetryAuthError(PermissionError):
    """Raised when a telemetry signature is missing, invalid, stale, revoked, or replayed."""


@dataclass(frozen=True)
class SignedTelemetryAuthConfig:
    max_age_seconds: int = 300
    max_future_seconds: int = 30

    def __post_init__(self) -> None:
        if not 1 <= self.max_age_seconds <= 900:
            raise ValueError("max_age_seconds must be between 1 and 900.")
        if not 0 <= self.max_future_seconds <= 120:
            raise ValueError("max_future_seconds must be between 0 and 120.")


class TelemetryCredentialRepository:
    """Tenant-scoped public-key credential lifecycle with no private-key storage."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _to_contract(row: TelemetryAgentCredentialRow) -> TelemetrySigningCredential:
        return TelemetrySigningCredential(
            credential_id=row.credential_id,
            tenant_id=str(row.tenant_id),
            agent_id=row.agent_id,
            key_id=row.key_id,
            public_key_pem=row.public_key_pem,
            status=row.status,
            created_at=row.created_at,
            revoked_at=row.revoked_at,
        )

    @staticmethod
    def _validate_public_key(public_key_pem: str) -> None:
        try:
            serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        except Exception as exc:
            raise ValueError("telemetry credential public_key_pem is not a valid public key.") from exc

    async def register(self, credential: TelemetrySigningCredential) -> tuple[TelemetrySigningCredential, bool]:
        if credential.status != "active" or credential.revoked_at is not None:
            raise ValueError("new telemetry credentials must be active and cannot be pre-revoked.")
        self._validate_public_key(credential.public_key_pem)
        tenant_uuid = UUID(credential.tenant_id)
        async with self._session_factory() as session:
            existing = await session.scalar(
                select(TelemetryAgentCredentialRow).where(
                    TelemetryAgentCredentialRow.tenant_id == tenant_uuid,
                    TelemetryAgentCredentialRow.agent_id == credential.agent_id,
                    TelemetryAgentCredentialRow.key_id == credential.key_id,
                )
            )
            if existing is not None:
                if existing.public_key_pem != credential.public_key_pem:
                    raise ValueError("telemetry credential key_id is already bound to different public key material.")
                return self._to_contract(existing), False
            row = TelemetryAgentCredentialRow(
                credential_id=credential.credential_id,
                tenant_id=tenant_uuid,
                agent_id=credential.agent_id,
                key_id=credential.key_id,
                public_key_pem=credential.public_key_pem,
                status="active",
                created_at=credential.created_at,
                revoked_at=None,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return self._to_contract(row), True

    async def list_for_tenant(self, tenant_id: str, *, limit: int = 200) -> list[TelemetrySigningCredential]:
        tenant_uuid = UUID(tenant_id)
        async with self._session_factory() as session:
            rows = (
                await session.scalars(
                    select(TelemetryAgentCredentialRow)
                    .where(TelemetryAgentCredentialRow.tenant_id == tenant_uuid)
                    .order_by(TelemetryAgentCredentialRow.created_at.desc())
                    .limit(limit)
                )
            ).all()
        return [self._to_contract(row) for row in rows]

    async def revoke(self, tenant_id: str, credential_id: str, *, revoked_at: datetime | None = None) -> TelemetrySigningCredential:
        tenant_uuid = UUID(tenant_id)
        timestamp = (revoked_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
        async with self._session_factory() as session:
            row = await session.scalar(
                select(TelemetryAgentCredentialRow).where(
                    TelemetryAgentCredentialRow.tenant_id == tenant_uuid,
                    TelemetryAgentCredentialRow.credential_id == credential_id,
                )
            )
            if row is None:
                raise LookupError("Signed telemetry credential was not found for the authenticated tenant.")
            if row.status == "active":
                row.status = "revoked"
                row.revoked_at = timestamp
                await session.commit()
                await session.refresh(row)
            return self._to_contract(row)


class SignedTelemetryAuthService:
    """Verifies one detached RSA signature and records its nonce before telemetry publication."""

    def __init__(
        self,
        *,
        session_factory: SessionFactory = AsyncSessionLocal,
        config: SignedTelemetryAuthConfig | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._config = config or SignedTelemetryAuthConfig()
        self._now = now or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def canonical_telemetry_body(event: Mapping[str, Any]) -> bytes:
        """Canonicalize the complete telemetry body without relying on request key ordering."""
        return json.dumps(dict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    @classmethod
    def payload_sha256(cls, event: Mapping[str, Any]) -> str:
        return sha256(cls.canonical_telemetry_body(event)).hexdigest()

    @staticmethod
    def canonical_signature_payload(envelope: SignedTelemetryEnvelope) -> bytes:
        payload = {
            "domain": TELEMETRY_SIGNATURE_DOMAIN,
            "tenant_id": envelope.tenant_id,
            "agent_id": envelope.agent_id,
            "key_id": envelope.key_id,
            "nonce": envelope.nonce,
            "signed_at": envelope.signed_at.isoformat(),
            "payload_sha256": envelope.payload_sha256,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

    def _parse_envelope(
        self,
        *,
        event: Mapping[str, Any],
        key_id: str | None,
        nonce: str | None,
        signed_at: str | None,
        signature: str | None,
    ) -> SignedTelemetryEnvelope:
        try:
            return SignedTelemetryEnvelope(
                tenant_id=str(event["tenant_id"]),
                agent_id=str(event["agent_id"]),
                key_id=key_id,
                nonce=nonce,
                signed_at=signed_at,
                payload_sha256=self.payload_sha256(event),
                signature=signature,
            )
        except (KeyError, ValidationError, TypeError, ValueError) as exc:
            raise SignedTelemetryAuthError("Signed telemetry headers or identity fields are invalid.") from exc

    def _verify_timestamp(self, envelope: SignedTelemetryEnvelope) -> None:
        now = self._now().astimezone(timezone.utc)
        if envelope.signed_at < now - timedelta(seconds=self._config.max_age_seconds):
            raise SignedTelemetryAuthError("Signed telemetry request is stale.")
        if envelope.signed_at > now + timedelta(seconds=self._config.max_future_seconds):
            raise SignedTelemetryAuthError("Signed telemetry timestamp is in the future.")

    async def verify_and_record(
        self,
        *,
        event: Mapping[str, Any],
        key_id: str | None,
        nonce: str | None,
        signed_at: str | None,
        signature: str | None,
    ) -> SignedTelemetryEnvelope:
        """Fail closed unless an active exact credential signs a fresh, unused request body."""
        envelope = self._parse_envelope(
            event=event,
            key_id=key_id,
            nonce=nonce,
            signed_at=signed_at,
            signature=signature,
        )
        self._verify_timestamp(envelope)
        tenant_uuid = UUID(envelope.tenant_id)

        async with self._session_factory() as session:
            credential = await session.scalar(
                select(TelemetryAgentCredentialRow).where(
                    TelemetryAgentCredentialRow.tenant_id == tenant_uuid,
                    TelemetryAgentCredentialRow.agent_id == envelope.agent_id,
                    TelemetryAgentCredentialRow.key_id == envelope.key_id,
                    TelemetryAgentCredentialRow.status == "active",
                    TelemetryAgentCredentialRow.revoked_at.is_(None),
                )
            )
            if credential is None:
                raise SignedTelemetryAuthError("No active signed telemetry credential matches this tenant, agent, and key.")

            try:
                signature_valid = verify_signature(
                    self.canonical_signature_payload(envelope),
                    envelope.signature,
                    credential.public_key_pem,
                )
            except Exception as exc:
                raise SignedTelemetryAuthError("Signed telemetry credential or signature is invalid.") from exc
            if not signature_valid:
                raise SignedTelemetryAuthError("Signed telemetry signature is invalid.")

            nonce_row = TelemetrySignatureNonceRow(
                nonce_record_id=str(uuid4()),
                tenant_id=tenant_uuid,
                agent_id=envelope.agent_id,
                key_id=envelope.key_id,
                nonce=envelope.nonce,
                payload_sha256=envelope.payload_sha256,
                signed_at=envelope.signed_at,
                accepted_at=self._now().astimezone(timezone.utc),
            )
            session.add(nonce_row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise SignedTelemetryAuthError("Signed telemetry nonce was already accepted; replay is forbidden.") from exc

        return envelope
