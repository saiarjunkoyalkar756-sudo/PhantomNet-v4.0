#!/usr/bin/env python3
"""Safe end-to-end operational dry-run for the Phase 2 Wazuh governed-response bridge.

This runner never opens a network connection, never starts Wazuh, and never changes an endpoint.
It uses the real containment service, Wazuh adapter, signed receipt service, and audit chain against
an in-memory SQLite database. A local simulated Wazuh client acknowledges only the fixed named
commands and a local simulated endpoint emits a signed receipt after dispatch.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sys
from uuid import uuid4

from _bootstrap import configure_script_imports

configure_script_imports()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.audit_log_collector.integrity import verify_chain
from backend_api.endpoint_inventory_service.forwarders import WazuhForwarderService
from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.wazuh_active_response_adapter import (
    WazuhActiveResponseConfig,
    WazuhActiveResponseContainmentAdapter,
)
from backend_api.soar_engine.wazuh_response_receipts import (
    WazuhReceiptConfig,
    WazuhResponseReceipt,
    WazuhResponseReceiptService,
)
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest, WazuhTelemetryBatch


TENANT_ID = "00000000-0000-0000-0000-000000000001"
WAZUH_AGENT_ID = "007"
AUDIT_HMAC_KEY_ID = "dry-run-containment-key-1"
COMMAND_HMAC_KEY_ID = "dry-run-wazuh-command-key-1"
RECEIPT_HMAC_KEY_ID = "dry-run-wazuh-receipt-key-1"


class SimulatedWazuhClient:
    """A deterministic local acknowledgement of only the bridge's two fixed command names."""

    def __init__(self) -> None:
        self.dispatches: list[dict[str, object]] = []

    def dispatch(self, *, agent_id: str, command: str, arguments: list[str], alert: dict[str, object]) -> dict[str, object]:
        if agent_id != WAZUH_AGENT_ID:
            raise RuntimeError("Dry-run simulated Wazuh rejected an unexpected agent target.")
        if command not in {"!phantomnet-network-isolate", "!phantomnet-network-release"}:
            raise RuntimeError("Dry-run simulated Wazuh rejected a non-allowlisted command.")
        if len(arguments) != 9 or arguments[0] != TENANT_ID or arguments[3] != WAZUH_AGENT_ID:
            raise RuntimeError("Dry-run simulated Wazuh rejected an invalid signed command envelope.")
        self.dispatches.append({"agent_id": agent_id, "command": command, "arguments": arguments, "alert": alert})
        return {
            "accepted": True,
            "wazuh_agent_id": agent_id,
            "affected_items": [agent_id],
            "total_failed_items": 0,
            "message": "Simulated Wazuh accepted the named command for the single allow-listed lab agent.",
        }


class SimulatedEndpointReceiptService:
    """Produces a fresh signed endpoint receipt only after the adapter asks for post-dispatch proof."""

    def __init__(self, service: WazuhResponseReceiptService, hmac_key: str) -> None:
        self._service = service
        self._hmac_key = hmac_key
        self._issued: set[tuple[str, str]] = set()
        self.receipt_ids: list[str] = []

    def _signed_receipt(
        self,
        *,
        tenant_id: str,
        request_id: str,
        approval_id: str,
        asset_id: str,
        action: str,
        expected_network_state: str,
        command_fingerprint: str,
    ) -> WazuhResponseReceipt:
        provisional = WazuhResponseReceipt(
            receipt_id=f"dry-run-receipt-{uuid4()}",
            tenant_id=tenant_id,
            request_id=request_id,
            approval_id=approval_id,
            asset_id=asset_id,
            wazuh_agent_id=asset_id,
            action=action,
            network_state=expected_network_state,
            command_fingerprint=command_fingerprint,
            nonce=f"dry-run-nonce-{uuid4()}",
            observed_at=datetime.now(timezone.utc),
            signature_key_id=RECEIPT_HMAC_KEY_ID,
            signature="0" * 64,
        )
        canonical = json.dumps(provisional.unsigned_payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return provisional.model_copy(
            update={"signature": hmac.new(self._hmac_key.encode("utf-8"), canonical, hashlib.sha256).hexdigest()}
        )

    async def find_verified_receipt(self, **kwargs):
        key = (str(kwargs["request_id"]), str(kwargs["action"]))
        if key not in self._issued:
            receipt = self._signed_receipt(
                tenant_id=str(kwargs["tenant_id"]),
                request_id=str(kwargs["request_id"]),
                approval_id=str(kwargs["approval_id"]),
                asset_id=str(kwargs["asset_id"]),
                action=str(kwargs["action"]),
                expected_network_state=str(kwargs["expected_network_state"]),
                command_fingerprint=str(kwargs["command_fingerprint"]),
            )
            stored = await self._service.submit(receipt)
            self._issued.add(key)
            self.receipt_ids.append(stored.receipt_id)
        return await self._service.find_verified_receipt(**kwargs)


def _artifact_path() -> Path:
    directory = Path(os.getenv("PHANTOMNET_WAZUH_DRY_RUN_ARTIFACT_DIR", "artifacts"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"wazuh_governed_response_dry_run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"


async def _run() -> dict[str, object]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        audit_hmac_key = secrets.token_urlsafe(32)
        command_hmac_key = secrets.token_urlsafe(32)
        receipt_hmac_key = secrets.token_urlsafe(32)
        receipt_store = WazuhResponseReceiptService(
            session_factory=sessions,
            config=WazuhReceiptConfig(hmac_key=receipt_hmac_key, key_id=RECEIPT_HMAC_KEY_ID),
        )
        simulated_wazuh = SimulatedWazuhClient()
        simulated_receipts = SimulatedEndpointReceiptService(receipt_store, receipt_hmac_key)
        adapter = WazuhActiveResponseContainmentAdapter(
            config=WazuhActiveResponseConfig(
                enabled=True,
                api_base_url="https://wazuh-dry-run.invalid:55000",
                username="simulated-wazuh-bridge",
                password="not-used-by-simulated-client",
                command_hmac_key=command_hmac_key,
                command_hmac_key_id=COMMAND_HMAC_KEY_ID,
                tenant_agent_allowlist={TENANT_ID: frozenset({WAZUH_AGENT_ID})},
                allowed_profiles=frozenset({"lab-network-isolation-v1"}),
                receipt_poll_interval_seconds=0.01,
            ),
            client=simulated_wazuh,
            receipt_service=simulated_receipts,
        )
        containment = GovernedContainmentService(
            session_factory=sessions,
            adapter=adapter,
            audit_signing_key=audit_hmac_key,
            audit_key_id=AUDIT_HMAC_KEY_ID,
        )
        inventory = EndpointInventoryRepository(sessions)
        forwarder = WazuhForwarderService(sessions, EndpointTelemetryIngestion(inventory))
        forwarder_record, forwarder_token = await forwarder.register(
            TENANT_ID, "wazuh-governed-response-dry-run", "dry-run-forwarder-operator"
        )
        wazuh_alert = {
            "id": "dry-run-wazuh-alert-001",
            "timestamp": "2026-08-19T06:00:00Z",
            "agent": {
                "id": WAZUH_AGENT_ID,
                "name": "dry-run-endpoint",
                "ip": "192.0.2.77",
                "os": {"name": "Ubuntu", "version": "24.04"},
            },
            "rule": {
                "id": "5710",
                "level": 10,
                "description": "Synthetic integrity alert for governed-response dry-run",
                "groups": ["syscheck"],
            },
            "syscheck": {
                "event": "modified",
                "path": "/etc/passwd",
                "sha256_before": "dry-run-before",
                "sha256_after": "dry-run-after",
            },
        }
        forwarder_result = await forwarder.stream_batch(
            forwarder_record.forwarder_id,
            forwarder_token,
            WazuhTelemetryBatch(batch_id="dry-run-wazuh-batch-001", sequence=1, alerts=[wazuh_alert]),
        )
        if (
            forwarder_result["asset_created"] != 1
            or forwarder_result["integrity_created"] != 1
            or forwarder_result["canonical_event_count"] != 2
            or forwarder_result["automatic_enforcement"]
        ):
            raise RuntimeError("Dry-run Wazuh telemetry did not produce the expected read-only asset and integrity evidence.")
        simulated_alert = {
            "source": "wazuh",
            "event_type": "wazuh.alert",
            "rule_id": wazuh_alert["rule"]["id"],
            "severity": "high",
            "agent_id": WAZUH_AGENT_ID,
            "message": wazuh_alert["rule"]["description"],
            "automatic_enforcement": False,
        }
        request, created = await containment.request(
            ContainmentRequest(
                tenant_id=TENANT_ID,
                action="isolate_endpoint",
                target=WAZUH_AGENT_ID,
                asset_id=WAZUH_AGENT_ID,
                playbook_id="wazuh-governed-response-dry-run",
                requested_by="dry-run-analyst",
                idempotency_key=f"wazuh-governed-dry-run-{uuid4()}",
                parameters={
                    "wazuh_agent_id": WAZUH_AGENT_ID,
                    "response_profile": "lab-network-isolation-v1",
                    "management_cidr": "192.0.2.0/24",
                    "verification_timeout_seconds": 5,
                },
                requires_approval=True,
                automatic_enforcement=False,
            )
        )
        if not created:
            raise RuntimeError("Dry-run request unexpectedly collided with an existing idempotency key.")
        approval = await containment.approve(
            ContainmentApproval(
                request_id=request.request_id,
                tenant_id=TENANT_ID,
                decision="approved",
                decided_by="dry-run-incident-commander",
                reason="Synthetic Wazuh alert scope and management path approved for non-network dry-run.",
            )
        )
        execution = await containment.execute(TENANT_ID, request.request_id, "dry-run-incident-commander")
        if execution.status != "verified" or not execution.rollback_available:
            raise RuntimeError(
                f"Dry-run isolate stage did not produce verified rollback-capable evidence: {execution.verification.get('detail', '')}"
            )
        rollback = await containment.rollback(TENANT_ID, request.request_id, "dry-run-incident-commander")
        if rollback.status != "rolled_back" or not rollback.rolled_back:
            raise RuntimeError(
                f"Dry-run release stage did not produce verified rollback evidence: {rollback.verification.get('detail', '')}"
            )

        async with sessions() as session:
            audit_rows = list(await session.scalars(select(ContainmentAuditRecordRow).order_by(ContainmentAuditRecordRow.id)))
        audit_records = [
            {
                "record_id": row.record_id,
                "timestamp": row.timestamp,
                "actor_id": row.actor_id,
                "action": row.action,
                "payload": row.payload,
                "previous_hash": row.previous_hash,
                "record_hash": row.record_hash,
                "signature": row.signature,
                "signature_key_id": row.signature_key_id,
            }
            for row in audit_rows
        ]
        audit_valid = verify_chain(
            audit_records,
            signing_key=audit_hmac_key,
            require_signature=True,
            expected_key_id=AUDIT_HMAC_KEY_ID,
        )
        if not audit_valid:
            raise RuntimeError("Dry-run containment audit chain did not verify.")
        if [item["command"] for item in simulated_wazuh.dispatches] != ["!phantomnet-network-isolate", "!phantomnet-network-release"]:
            raise RuntimeError("Dry-run did not dispatch exactly the governed isolate and release commands.")
        if len(simulated_receipts.receipt_ids) != 2:
            raise RuntimeError("Dry-run did not produce distinct isolate and release endpoint receipts.")

        return {
            "status": "passed",
            "scope": "isolated_sqlite_simulated_wazuh_no_network_no_endpoint_change",
            "simulated_wazuh_alert": simulated_alert,
            "telemetry_evidence": {
                "forwarder_id": forwarder_record.forwarder_id,
                "batch_id": forwarder_result["batch_id"],
                "sequence": forwarder_result["sequence"],
                "asset_created": forwarder_result["asset_created"],
                "integrity_created": forwarder_result["integrity_created"],
                "canonical_event_count": forwarder_result["canonical_event_count"],
                "adapter_mode": forwarder_result["adapter_mode"],
                "automatic_enforcement": forwarder_result["automatic_enforcement"],
            },
            "request_id": request.request_id,
            "approval_id": approval.approval_id,
            "execution_status": execution.status,
            "rollback_status": rollback.status,
            "wazuh_commands": [item["command"] for item in simulated_wazuh.dispatches],
            "receipt_ids": simulated_receipts.receipt_ids,
            "audit_record_count": len(audit_records),
            "audit_chain_valid": audit_valid,
            "safety": {
                "network_calls": False,
                "external_wazuh": False,
                "endpoint_actions": False,
                "automatic_enforcement": False,
            },
        }
    finally:
        await engine.dispose()


def main() -> int:
    result = asyncio.run(_run())
    artifact = _artifact_path()
    artifact.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "artifact": str(artifact), "audit_chain_valid": result["audit_chain_valid"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
