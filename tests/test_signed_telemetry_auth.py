from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.shared.database import Base, TelemetryAgentCredentialRow, TelemetrySignatureNonceRow, Tenant
from backend_api.shared.security_utils import generate_key_pair, sign_data
from backend_api.telemetry_ingestor import main as telemetry_main
from backend_api.telemetry_ingestor.main import TelemetryEvent
from backend_api.telemetry_ingestor.signed_auth import (
    SignedTelemetryAuthConfig,
    SignedTelemetryAuthError,
    SignedTelemetryAuthService,
)


TENANT_ID = UUID("00000000-0000-0000-0000-000000000101")
OTHER_TENANT_ID = UUID("00000000-0000-0000-0000-000000000102")
AGENT_ID = "agent-lab-001"
KEY_ID = "lab-key-0001"
NOW = datetime(2026, 8, 23, 9, 0, tzinfo=timezone.utc)


async def _service_and_keys():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    private_key, public_key = generate_key_pair()
    async with sessions() as session:
        session.add_all([
            Tenant(id=TENANT_ID, name="signed-telemetry-tenant"),
            Tenant(id=OTHER_TENANT_ID, name="other-signed-telemetry-tenant"),
            TelemetryAgentCredentialRow(
                credential_id="credential-lab-001",
                tenant_id=TENANT_ID,
                agent_id=AGENT_ID,
                key_id=KEY_ID,
                public_key_pem=public_key,
                status="active",
            ),
        ])
        await session.commit()
    service = SignedTelemetryAuthService(
        session_factory=sessions,
        config=SignedTelemetryAuthConfig(max_age_seconds=300, max_future_seconds=30),
        now=lambda: NOW,
    )
    return service, sessions, engine, private_key


def _event(*, tenant_id: UUID = TENANT_ID, event_type: str = "agent_health") -> dict:
    return {
        "tenant_id": str(tenant_id),
        "agent_id": AGENT_ID,
        "timestamp": NOW.isoformat(),
        "event_type": event_type,
        "data": {"fixture": "signed-telemetry", "status": "healthy"},
    }


def _signed_headers(service: SignedTelemetryAuthService, private_key: str, event: dict, nonce: str = "nonce-signed-telemetry-0001") -> dict:
    payload_sha256 = service.payload_sha256(event)
    unsigned_envelope = {
        "tenant_id": event["tenant_id"],
        "agent_id": event["agent_id"],
        "key_id": KEY_ID,
        "nonce": nonce,
        "signed_at": NOW,
        "payload_sha256": payload_sha256,
        "signature": "0" * 64,
    }
    from phantomnet_core.contracts import SignedTelemetryEnvelope

    envelope = SignedTelemetryEnvelope(**unsigned_envelope)
    signature = sign_data(service.canonical_signature_payload(envelope), private_key)
    return {
        "key_id": KEY_ID,
        "nonce": nonce,
        "signed_at": NOW.isoformat(),
        "signature": signature,
    }


@pytest.mark.asyncio
async def test_valid_signed_telemetry_is_bound_to_active_tenant_agent_key_and_nonce():
    service, sessions, engine, private_key = await _service_and_keys()
    try:
        event = _event()
        envelope = await service.verify_and_record(event=event, **_signed_headers(service, private_key, event))

        assert envelope.tenant_id == str(TENANT_ID)
        assert envelope.agent_id == AGENT_ID
        async with sessions() as session:
            rows = (await session.scalars(select(TelemetrySignatureNonceRow))).all()
        assert len(rows) == 1
        assert rows[0].payload_sha256 == service.payload_sha256(event)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_signed_telemetry_replay_and_body_tampering_are_rejected():
    service, _sessions, engine, private_key = await _service_and_keys()
    try:
        event = _event()
        headers = _signed_headers(service, private_key, event)
        await service.verify_and_record(event=event, **headers)

        with pytest.raises(SignedTelemetryAuthError, match="replay"):
            await service.verify_and_record(event=event, **headers)

        altered = {**event, "data": {**event["data"], "status": "altered"}}
        with pytest.raises(SignedTelemetryAuthError, match="signature"):
            await service.verify_and_record(event=altered, **_signed_headers(service, private_key, event, nonce="nonce-signed-telemetry-0002"))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_signed_telemetry_rejects_stale_and_future_timestamps():
    service, _sessions, engine, private_key = await _service_and_keys()
    try:
        event = _event()
        stale_time = NOW.replace(hour=8, minute=54)
        future_time = NOW.replace(minute=1, hour=10)
        for signed_at, expected_message, nonce in (
            (stale_time, "stale", "nonce-signed-telemetry-stale"),
            (future_time, "future", "nonce-signed-telemetry-future"),
        ):
            headers = _signed_headers(service, private_key, event, nonce=nonce)
            headers["signed_at"] = signed_at.isoformat()
            from phantomnet_core.contracts import SignedTelemetryEnvelope

            unsigned = SignedTelemetryEnvelope(
                tenant_id=event["tenant_id"],
                agent_id=event["agent_id"],
                key_id=KEY_ID,
                nonce=nonce,
                signed_at=signed_at,
                payload_sha256=service.payload_sha256(event),
                signature="0" * 64,
            )
            headers["signature"] = sign_data(service.canonical_signature_payload(unsigned), private_key)
            with pytest.raises(SignedTelemetryAuthError, match=expected_message):
                await service.verify_and_record(event=event, **headers)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_signed_telemetry_rejects_cross_tenant_and_revoked_credential_attempts():
    service, sessions, engine, private_key = await _service_and_keys()
    try:
        cross_tenant = _event(tenant_id=OTHER_TENANT_ID)
        with pytest.raises(SignedTelemetryAuthError, match="No active"):
            await service.verify_and_record(event=cross_tenant, **_signed_headers(service, private_key, cross_tenant))

        async with sessions() as session:
            credential = await session.scalar(select(TelemetryAgentCredentialRow).where(TelemetryAgentCredentialRow.credential_id == "credential-lab-001"))
            assert credential is not None
            credential.status = "revoked"
            credential.revoked_at = NOW
            await session.commit()

        event = _event()
        with pytest.raises(SignedTelemetryAuthError, match="No active"):
            await service.verify_and_record(event=event, **_signed_headers(service, private_key, event))
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_accepted_nonce_rows_are_immutable():
    service, sessions, engine, private_key = await _service_and_keys()
    try:
        event = _event()
        await service.verify_and_record(event=event, **_signed_headers(service, private_key, event))
        async with sessions() as session:
            row = await session.scalar(select(TelemetrySignatureNonceRow))
            assert row is not None
            row.nonce = "mutation-is-forbidden"
            with pytest.raises(RuntimeError, match="immutable"):
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_ingest_handler_rejects_unsigned_before_broker_use(monkeypatch):
    event = TelemetryEvent(**_event())

    def unexpected_broker_access():
        raise AssertionError("Unsigned telemetry must not initialize or use a broker producer.")

    monkeypatch.setattr(telemetry_main, "get_kafka_producer", unexpected_broker_access)
    response = await telemetry_main.ingest_telemetry(
        event,
        x_phantomnet_key_id=None,
        x_phantomnet_nonce=None,
        x_phantomnet_signed_at=None,
        x_phantomnet_signature=None,
    )

    assert response.status_code == 403
    assert b"SIGNED_TELEMETRY_REJECTED" in response.body


@pytest.mark.asyncio
async def test_ingest_handler_publishes_only_after_valid_signature(monkeypatch):
    service, _sessions, engine, private_key = await _service_and_keys()
    published: list[tuple[str, dict]] = []

    class FakeProducer:
        def send(self, topic: str, body: dict) -> None:
            published.append((topic, body))

    try:
        event_body = _event()
        event = TelemetryEvent(**event_body)
        monkeypatch.setattr(telemetry_main, "telemetry_auth_service", service)
        monkeypatch.setattr(telemetry_main, "get_kafka_producer", lambda: FakeProducer())
        response = await telemetry_main.ingest_telemetry(event, **{
            f"x_phantomnet_{name}": value
            for name, value in _signed_headers(service, private_key, event_body).items()
        })

        assert response["success"] is True
        assert response["data"] == {"status": "ingested"}
        assert len(published) == 1
        assert published[0][1]["tenant_id"] == str(TENANT_ID)
    finally:
        await engine.dispose()


def test_telemetry_event_requires_explicit_tenant_id():
    with pytest.raises(Exception):
        TelemetryEvent(
            agent_id=AGENT_ID,
            timestamp=NOW.isoformat(),
            event_type="agent_health",
            data={"fixture": "missing-tenant"},
        )
