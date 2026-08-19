"""Phase 7 isolated SOC benchmark.

This harness uses a temporary SQLite database and simulated adapters only. It makes no external
network calls, sends no agent commands, and executes no firewall or endpoint action. Results are
for regression comparison in this sandbox, not a production capacity claim.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import statistics
import tempfile
import time
from pathlib import Path

from _bootstrap import configure_script_imports

configure_script_imports()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.audit_log_collector.integrity import verify_chain
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.endpoint_inventory_service.forwarders import WazuhForwarderService
from backend_api.endpoint_inventory_service.ingestion import EndpointTelemetryIngestion
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest, EventEnvelope, WazuhTelemetryBatch


TENANT_ID = "00000000-0000-0000-0000-000000000001"
PIPELINE_SAMPLE_COUNT = 120
WAZUH_BATCH_SIZE = 25


class BenchmarkContainmentAdapter:
    name = "benchmark-simulated-containment"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def execute(self, _request, _approval):
        self.calls.append("execute")
        return {"enforced": True, "verified": True, "rollback_available": True, "detail": "Simulated only."}

    def rollback(self, _request, _approval):
        self.calls.append("rollback")
        return {"enforced": False, "verified": True, "detail": "Simulated only."}


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * percentile)))
    return ordered[index]


def _wazuh_alert(index: int) -> dict[str, object]:
    return {
        "id": f"benchmark-wazuh-{index}",
        "timestamp": "2026-08-18T19:00:00Z",
        "agent": {"id": "benchmark-agent", "name": "benchmark-host", "ip": "10.0.0.77", "os": {"name": "Ubuntu", "version": "24.04"}},
        "rule": {"id": "550", "level": 10, "description": "Controlled integrity event", "groups": ["syscheck"]},
        "syscheck": {"event": "modified", "path": f"/tmp/benchmark-{index}.txt", "sha256_before": "before", "sha256_after": "after"},
    }


async def main() -> None:
    signing_key = secrets.token_urlsafe(32)
    key_id = "benchmark-ephemeral"
    with tempfile.TemporaryDirectory(prefix="phantomnet-phase7-") as temporary:
        engine = create_async_engine(f"sqlite+aiosqlite:///{Path(temporary) / 'benchmark.db'}")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            sessions = async_sessionmaker(engine, expire_on_commit=False)
            detections = DetectionRepository(sessions)
            alerts = AlertWorkflow(sessions)
            processor = CanonicalBrokerProcessor(detections, alert_workflow=alerts)
            endpoint_repository = EndpointInventoryRepository(sessions)
            endpoint_ingestion = EndpointTelemetryIngestion(endpoint_repository)
            forwarders = WazuhForwarderService(sessions, endpoint_ingestion)
            adapter = BenchmarkContainmentAdapter()
            containment = GovernedContainmentService(sessions, adapter, signing_key, key_id)

            for warmup in range(10):
                event = EventEnvelope(tenant_id=TENANT_ID, source="bas-engine", event_type="auth_attempt", severity="high", payload={"scenario_id": "BAS-AUTH-001", "source_ip": "198.51.100.42", "failed_attempts": 5, "warmup": warmup}, correlation_id=f"warmup-{warmup}", tags=["bas", "controlled", "non-destructive"], provenance={"execution": "telemetry-fixture"})
                await processor.process(normalize_event(event.model_dump(mode="json")))

            latencies_ms: list[float] = []
            started_pipeline = time.perf_counter()
            for index in range(PIPELINE_SAMPLE_COUNT):
                event = EventEnvelope(tenant_id=TENANT_ID, source="bas-engine", event_type="auth_attempt", severity="high", payload={"scenario_id": "BAS-AUTH-001", "source_ip": "198.51.100.42", "failed_attempts": 5, "sample": index}, correlation_id=f"benchmark-{index}", tags=["bas", "controlled", "non-destructive"], provenance={"execution": "telemetry-fixture"})
                started = time.perf_counter()
                result = await processor.process(normalize_event(event.model_dump(mode="json")))
                latencies_ms.append((time.perf_counter() - started) * 1000)
                assert len(result.created_detection_ids) == 1
            pipeline_elapsed = time.perf_counter() - started_pipeline

            forwarder, token = await forwarders.register(TENANT_ID, "benchmark-forwarder", "benchmark-admin")
            started_wazuh = time.perf_counter()
            streamed = await forwarders.stream_batch(
                forwarder.forwarder_id,
                token,
                WazuhTelemetryBatch(batch_id="benchmark-wazuh-batch-0001", sequence=1, alerts=[_wazuh_alert(index) for index in range(WAZUH_BATCH_SIZE)]),
            )
            wazuh_elapsed_ms = (time.perf_counter() - started_wazuh) * 1000

            asset = (await endpoint_repository.list_assets(TENANT_ID))[0]
            request, _ = await containment.request(
                ContainmentRequest(tenant_id=TENANT_ID, action="isolate_endpoint", target=asset.hostname, asset_id=asset.asset_id, requested_by="benchmark-analyst", idempotency_key="benchmark-containment-idempotency-0001", parameters={"simulation": True}, requires_approval=True, automatic_enforcement=False)
            )
            await containment.approve(ContainmentApproval(request_id=request.request_id, tenant_id=TENANT_ID, decision="approved", decided_by="benchmark-approver", reason="Controlled benchmark approval."))
            started_containment = time.perf_counter()
            execution = await containment.execute(TENANT_ID, request.request_id, "benchmark-approver")
            rollback = await containment.rollback(TENANT_ID, request.request_id, "benchmark-approver")
            containment_elapsed_ms = (time.perf_counter() - started_containment) * 1000

            async with sessions() as session:
                audit_rows = list(await session.scalars(select(ContainmentAuditRecordRow).where(ContainmentAuditRecordRow.tenant_id == TENANT_ID).order_by(ContainmentAuditRecordRow.id)))
            audit_records = [{"record_id": row.record_id, "timestamp": row.timestamp, "actor_id": row.actor_id, "action": row.action, "payload": row.payload, "previous_hash": row.previous_hash, "record_hash": row.record_hash, "signature": row.signature, "signature_key_id": row.signature_key_id} for row in audit_rows]
            audit_valid = verify_chain(audit_records, signing_key=signing_key, require_signature=True, expected_key_id=key_id)
            results = {
                "environment": "isolated_sqlite_and_simulated_adapters",
                "external_calls": 0,
                "endpoint_actions": 0,
                "pipeline": {
                    "samples": PIPELINE_SAMPLE_COUNT,
                    "throughput_events_per_second": round(PIPELINE_SAMPLE_COUNT / pipeline_elapsed, 2),
                    "latency_ms": {"p50": round(statistics.median(latencies_ms), 3), "p95": round(_percentile(latencies_ms, 0.95), 3), "p99": round(_percentile(latencies_ms, 0.99), 3), "max": round(max(latencies_ms), 3)},
                },
                "wazuh_stream": {"batch_size": WAZUH_BATCH_SIZE, "latency_ms": round(wazuh_elapsed_ms, 3), "canonical_event_count": streamed["canonical_event_count"], "integrity_created": streamed["integrity_created"], "automatic_enforcement": streamed["automatic_enforcement"]},
                "containment_governance": {"latency_ms": round(containment_elapsed_ms, 3), "execution_status": execution.status, "rollback_status": rollback.status, "adapter_calls": adapter.calls, "audit_record_count": len(audit_records), "audit_chain_valid": audit_valid},
                "limitations": ["In-memory application components and temporary SQLite only.", "No Kafka/Redpanda, PostgreSQL, Redis, Neo4j, Docker Compose, endpoint agent, or external provider was exercised.", "Results are regression evidence, not a production sizing or throughput commitment."],
            }
            output_path = Path("artifacts/phase7_canonical_soc_benchmark.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(results, sort_keys=True))
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
