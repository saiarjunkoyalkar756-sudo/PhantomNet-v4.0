"""Run a controlled in-memory canonical ingestion stress benchmark.

The script uses only SQLite in memory and BAS-marked synthetic telemetry. It does not open a
network connection, contact an external broker, or execute a response adapter.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from _bootstrap import configure_script_imports

configure_script_imports()

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base
from phantomnet_core.contracts import EventEnvelope


TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _event(index: int) -> dict:
    return EventEnvelope(
        event_id=f"resilience-benchmark-{index:05d}",
        tenant_id=TENANT_ID,
        timestamp=datetime.now(timezone.utc),
        source="bas-engine",
        event_type="auth_attempt",
        severity="high",
        correlation_id=f"resilience-benchmark-correlation-{index:05d}",
        payload={
            "scenario_id": "BAS-AUTH-001",
            "source_ip": "198.51.100.42",
            "failed_attempts": 5,
            "sample": index,
        },
        tags=["bas", "controlled", "non-destructive", "resilience"],
        provenance={"execution": "telemetry-fixture", "benchmark": "isolated"},
    ).model_dump(mode="json")


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * fraction) - 1))
    return ordered[index]


async def run(event_count: int) -> dict:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        repository = DetectionRepository(sessions)
        workflow = AlertWorkflow(sessions)
        processor = CanonicalBrokerProcessor(repository, alert_workflow=workflow)
        messages = [normalize_event(_event(index)) for index in range(event_count)]
        latencies_ms: list[float] = []
        started = time.perf_counter()
        for message in messages:
            point = time.perf_counter()
            result = await processor.process(message)
            latencies_ms.append((time.perf_counter() - point) * 1000)
            if len(result.created_detection_ids) != 1:
                raise RuntimeError("A unique controlled stress event did not produce exactly one detection.")
        duration_s = time.perf_counter() - started

        duplicate_count = 0
        for message in messages[::10]:
            result = await processor.process(message)
            if result.created_detection_ids or len(result.duplicate_detection_ids) != 1:
                raise RuntimeError("A duplicate controlled delivery did not preserve idempotency.")
            duplicate_count += 1

        detections = await repository.list_for_tenant(TENANT_ID, limit=event_count + duplicate_count + 10)
        alerts = await workflow.list_for_tenant(TENANT_ID, limit=event_count + duplicate_count + 10)
        if len(detections) != event_count or len(alerts) != event_count:
            raise RuntimeError("Duplicate delivery changed durable detection or alert cardinality.")
        if any(alert.occurrence_count != 1 for alert in alerts):
            raise RuntimeError("Duplicate delivery inflated an analyst alert occurrence count.")
        return {
            "mode": "isolated_sqlite_bas_fixture",
            "external_actions": False,
            "event_count": event_count,
            "duplicate_delivery_count": duplicate_count,
            "unique_detection_count": len(detections),
            "unique_alert_count": len(alerts),
            "duration_seconds": round(duration_s, 6),
            "throughput_events_per_second": round(event_count / duration_s, 3),
            "latency_ms": {
                "p50": round(median(latencies_ms), 3),
                "p95": round(_percentile(latencies_ms, 0.95), 3),
                "p99": round(_percentile(latencies_ms, 0.99), 3),
            },
            "invariants": {
                "unique_detection_per_event": True,
                "unique_alert_per_event": True,
                "duplicate_delivery_idempotent": True,
                "response_adapter_executed": False,
            },
        }
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run controlled PhantomNet canonical-ingestion resilience stress validation.")
    parser.add_argument("--events", type=int, default=500, choices=range(1, 2001))
    parser.add_argument("--output", type=Path, default=Path("artifacts/resilience_stress_benchmark.json"))
    args = parser.parse_args()
    report = asyncio.run(run(args.events))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
