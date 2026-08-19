from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.response_adapter_router import GovernedResponseAdapterRouter
from backend_api.soar_engine.wazuh_active_response_adapter import (
    WazuhActiveResponseConfig,
    WazuhActiveResponseContainmentAdapter,
)
from backend_api.soar_engine.wazuh_response_receipts import (
    WazuhReceiptConfig,
    WazuhResponseReceipt,
    WazuhResponseReceiptService,
)
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


TENANT_ID = "00000000-0000-0000-0000-000000000001"
NOW = datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc)
HMAC_KEY = "wazuh-receipt-test-key"
KEY_ID = "wazuh-test-key-1"


class RecordingWazuhClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def dispatch(self, *, agent_id: str, command: str, arguments: list[str], alert: dict) -> dict:
        self.calls.append({"agent_id": agent_id, "command": command, "arguments": arguments, "alert": alert})
        return {"accepted": True, "wazuh_agent_id": agent_id, "affected_items": [agent_id], "total_failed_items": 0}


class MissingReceiptService:
    async def find_verified_receipt(self, **_kwargs):
        return None


class AdvancingClock:
    def __init__(self) -> None:
        self._calls = 0

    def __call__(self) -> datetime:
        value = NOW + timedelta(seconds=self._calls)
        self._calls += 1
        return value


async def _no_wait(_seconds: float) -> None:
    return None


class MatchingReceiptService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def find_verified_receipt(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(receipt_id="receipt-0000000001", observed_at=NOW)


def _bridge_config(*, enabled: bool = True) -> WazuhActiveResponseConfig:
    return WazuhActiveResponseConfig(
        enabled=enabled,
        api_base_url="https://wazuh.lab.example:55000",
        username="bridge-service",
        password="not-a-real-secret",
        command_hmac_key="wazuh-command-test-key",
        command_hmac_key_id="wazuh-command-test-key-1",
        tenant_agent_allowlist={TENANT_ID: frozenset({"007"})},
        allowed_profiles=frozenset({"lab-network-isolation-v1"}),
    )


def _request(*, action: str = "isolate_endpoint", idempotency_key: str = "wazuh-bridge-idempotency-0001") -> ContainmentRequest:
    return ContainmentRequest(
        tenant_id=TENANT_ID,
        action=action,
        target="007",
        asset_id="007",
        requested_by="analyst-1",
        idempotency_key=idempotency_key,
        parameters={
            "wazuh_agent_id": "007",
            "response_profile": "lab-network-isolation-v1",
            "management_cidr": "192.0.2.0/24",
            "verification_timeout_seconds": 3,
        },
        requires_approval=True,
        automatic_enforcement=False,
    )


def _approval(request: ContainmentRequest) -> ContainmentApproval:
    return ContainmentApproval(
        request_id=request.request_id,
        tenant_id=TENANT_ID,
        decision="approved",
        decided_by="incident-commander",
        reason="Scope, management path, and target were independently checked.",
    )


async def _service(adapter):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    return GovernedContainmentService(
        session_factory=sessions,
        adapter=adapter,
        audit_signing_key="containment-audit-test-key",
        audit_key_id="containment-test-key-1",
    ), sessions, engine


def _signed_receipt(request: ContainmentRequest, approval: ContainmentApproval, *, signature: str = "0" * 64) -> WazuhResponseReceipt:
    receipt = WazuhResponseReceipt(
        receipt_id="receipt-0000000001",
        tenant_id=TENANT_ID,
        request_id=request.request_id,
        approval_id=approval.approval_id,
        asset_id="007",
        wazuh_agent_id="007",
        action="isolate_endpoint",
        network_state="isolated",
        command_fingerprint="a" * 64,
        nonce="nonce-000000000001",
        observed_at=NOW,
        signature_key_id=KEY_ID,
        signature=signature,
    )
    canonical = json.dumps(receipt.unsigned_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return receipt.model_copy(update={"signature": hmac.new(HMAC_KEY.encode("utf-8"), canonical, hashlib.sha256).hexdigest()})


@pytest.mark.asyncio
async def test_wazuh_bridge_requires_explicit_enablement_and_never_contacts_wazuh_when_disabled():
    client = RecordingWazuhClient()
    adapter = WazuhActiveResponseContainmentAdapter(
        config=_bridge_config(enabled=False),
        client=client,
        receipt_service=MatchingReceiptService(),
        now=lambda: NOW,
    )

    result = await adapter.execute(_request(), _approval(_request()))

    assert result["enforced"] is False
    assert result["verified"] is False
    assert "disabled by default" in result["detail"]
    assert client.calls == []


@pytest.mark.asyncio
async def test_wazuh_bridge_rejects_missing_command_signature_configuration_before_dispatch():
    client = RecordingWazuhClient()
    adapter = WazuhActiveResponseContainmentAdapter(
        config=replace(_bridge_config(), command_hmac_key=None),
        client=client,
        receipt_service=MatchingReceiptService(),
        now=lambda: NOW,
    )

    result = await adapter.execute(_request(), _approval(_request()))

    assert result["enforced"] is False
    assert result["verified"] is False
    assert "command HMAC key" in result["detail"]
    assert client.calls == []


@pytest.mark.asyncio
async def test_wazuh_acknowledgement_without_fresh_signed_receipt_fails_closed():
    request = _request()
    approval = _approval(request)
    client = RecordingWazuhClient()
    adapter = WazuhActiveResponseContainmentAdapter(
        config=_bridge_config(),
        client=client,
        receipt_service=MissingReceiptService(),
        now=AdvancingClock(),
        sleep=_no_wait,
    )

    result = await adapter.execute(request, approval)

    assert client.calls
    assert result["enforced"] is False
    assert result["verified"] is False
    assert result["rollback_available"] is False
    assert "no fresh matching signed endpoint receipt" in result["detail"]


@pytest.mark.asyncio
async def test_wazuh_bridge_dispatches_exact_named_command_then_requires_matching_signed_receipt():
    request = _request()
    approval = _approval(request)
    client = RecordingWazuhClient()
    receipts = MatchingReceiptService()
    adapter = WazuhActiveResponseContainmentAdapter(
        config=_bridge_config(),
        client=client,
        receipt_service=receipts,
        now=lambda: NOW,
    )

    result = await adapter.execute(request, approval)

    assert result["enforced"] is True
    assert result["verified"] is True
    assert result["rollback_available"] is True
    assert client.calls[0]["agent_id"] == "007"
    assert client.calls[0]["command"] == "!phantomnet-network-isolate"
    assert client.calls[0]["arguments"][:4] == [TENANT_ID, request.request_id, approval.approval_id, "007"]
    assert receipts.calls[0]["expected_network_state"] == "isolated"
    assert result["wazuh"]["receipt_id"] == "receipt-0000000001"


@pytest.mark.asyncio
async def test_governed_wazuh_lifecycle_records_full_verification_evidence_and_release_rollback():
    client = RecordingWazuhClient()
    adapter = WazuhActiveResponseContainmentAdapter(
        config=_bridge_config(),
        client=client,
        receipt_service=MatchingReceiptService(),
        now=lambda: NOW,
    )
    service, sessions, engine = await _service(adapter)
    try:
        requested, _ = await service.request(_request())
        approved = await service.approve(_approval(requested))
        execution = await service.execute(TENANT_ID, requested.request_id, "incident-commander")
        rollback = await service.rollback(TENANT_ID, requested.request_id, "incident-commander")

        assert execution.status == "verified"
        assert execution.verification["wazuh"]["command"] == "!phantomnet-network-isolate"
        assert rollback.status == "rolled_back"
        assert client.calls[1]["command"] == "!phantomnet-network-release"
        async with sessions() as session:
            audit_rows = list(await session.scalars(select(ContainmentAuditRecordRow).order_by(ContainmentAuditRecordRow.id)))
        assert audit_rows[-2].payload["verification"]["wazuh"]["receipt_id"] == "receipt-0000000001"
        assert audit_rows[-1].payload["verification"]["wazuh"]["command"] == "!phantomnet-network-release"
        assert all(row.signature and row.signature_key_id == "containment-test-key-1" for row in audit_rows)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_signed_response_receipt_requires_approved_binding_and_rejects_replay():
    service, sessions, engine = await _service(adapter=type("Noop", (), {"name": "noop", "execute": lambda *_: {"enforced": False, "verified": False}, "rollback": lambda *_: {"enforced": False, "verified": False}})())
    try:
        request, _ = await service.request(_request(idempotency_key="wazuh-bridge-idempotency-0002"))
        approval = await service.approve(_approval(request))
        receipt_service = WazuhResponseReceiptService(
            session_factory=sessions,
            config=WazuhReceiptConfig(hmac_key=HMAC_KEY, key_id=KEY_ID),
            now=lambda: NOW,
        )
        receipt = _signed_receipt(request, approval)

        stored = await receipt_service.submit(receipt)
        assert stored.receipt_id == receipt.receipt_id
        with pytest.raises(PermissionError, match="already accepted"):
            await receipt_service.submit(receipt)

        bad_receipt = receipt.model_copy(update={"receipt_id": "receipt-0000000002", "nonce": "nonce-000000000002", "signature": "b" * 64})
        with pytest.raises(PermissionError, match="signature is invalid"):
            await receipt_service.submit(bad_receipt)
    finally:
        await engine.dispose()


def test_router_selects_wazuh_only_for_explicit_wazuh_parameters():
    wazuh_adapter = object()
    router = GovernedResponseAdapterRouter(
        endpoint_adapter=object(),
        aws_security_group_adapter=object(),
        wazuh_active_response_adapter=wazuh_adapter,
    )
    assert router._adapter_for(_request()) is wazuh_adapter
