"""Stage-level profiler for the isolated canonical SOC pipeline.

This tool uses a temporary SQLite database and controlled BAS-style fixtures. It performs no
network, endpoint, firewall, Wazuh active-response, or external-provider action. Results are
regression diagnostics, not production capacity claims.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import tempfile
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.bas_engine.detection_pipeline import evaluate_normalized_baseline_event
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.correlation_engine.ingestion import CanonicalBrokerProcessor
from backend_api.event_normalizer.main import normalize_event
from backend_api.shared.database import Base
from phantomnet_core.contracts import EventEnvelope


TENANT_ID = "00000000-0000-0000-0000-000000000001"
WARMUP_COUNT = 20
SAMPLE_COUNT = 150


def _event(index: int, phase: str) -> EventEnvelope:
    return EventEnvelope(
        tenant_id=TENANT_ID,
        source="bas-engine",
        event_type="auth_attempt",
        severity="high",
        payload={
            "scenario_id": "BAS-AUTH-001",
            "source_ip": "198.51.100.42",
            "failed_attempts": 5,
            "sample": index,
            "phase": phase,
        },
        correlation_id=f"profile-{phase}-{index}",
        tags=["bas", "controlled", "non-destructive"],
        provenance={"execution": "telemetry-fixture"},
    )


def _summary(values_ms: list[float]) -> dict[str, float]:
    ordered = sorted(values_ms)

    def percentile(value: float) -> float:
        return ordered[max(0, min(len(ordered) - 1, round((len(ordered) - 1) * value)))]

    return {
        "p50": round(statistics.median(ordered), 3),
        "p95": round(percentile(0.95), 3),
        "p99": round(percentile(0.99), 3),
        "mean": round(statistics.fmean(ordered), 3),
        "max": round(max(ordered), 3),
    }


async def _sample_async(operation: Callable[[int], Awaitable[None]]) -> dict[str, float]:
    for index in range(WARMUP_COUNT):
        await operation(-(index + 1))
    latencies_ms: list[float] = []
    for index in range(SAMPLE_COUNT):
        started = time.perf_counter()
        await operation(index)
        latencies_ms.append((time.perf_counter() - started) * 1000)
    return _summary(latencies_ms)


async def _sample_sync(operation: Callable[[int], None]) -> dict[str, float]:
    for index in range(WARMUP_COUNT):
        operation(-(index + 1))
    latencies_ms: list[float] = []
    for index in range(SAMPLE_COUNT):
        started = time.perf_counter()
        operation(index)
        latencies_ms.append((time.perf_counter() - started) * 1000)
    return _summary(latencies_ms)


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="phantomnet-profile-") as temporary:
        engine = create_async_engine(f"sqlite+aiosqlite:///{Path(temporary) / 'profile.db'}")
        try:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            sessions = async_sessionmaker(engine, expire_on_commit=False)
            detections = DetectionRepository(sessions)
            alerts = AlertWorkflow(sessions)
            processor = CanonicalBrokerProcessor(detections, alert_workflow=alerts)

            normalization = await _sample_sync(
                lambda index: normalize_event(_event(index, "normalization").model_dump(mode="json"))
            )
            evaluation = await _sample_sync(
                lambda index: evaluate_normalized_baseline_event(
                    normalize_event(_event(index, "evaluation").model_dump(mode="json"))
                )
            )

            async def persist(index: int) -> None:
                detection = evaluate_normalized_baseline_event(
                    normalize_event(_event(index, "persistence").model_dump(mode="json"))
                )
                assert detection is not None
                _, created = await detections.persist(detection)
                assert created

            persistence = await _sample_async(persist)

            async def alert(index: int) -> None:
                detection = evaluate_normalized_baseline_event(
                    normalize_event(_event(index, "alert").model_dump(mode="json"))
                )
                assert detection is not None
                workflow = await alerts.ingest_detection(detection)
                assert workflow.created

            alert_creation = await _sample_async(alert)

            async def full_pipeline(index: int) -> None:
                result = await processor.process(
                    normalize_event(_event(index, "pipeline").model_dump(mode="json"))
                )
                assert len(result.created_detection_ids) == 1
                assert len(result.alert_workflows) == 1

            full_pipeline_result = await _sample_async(full_pipeline)
            result = {
                "environment": "temporary_sqlite_and_controlled_bas_fixtures",
                "external_calls": 0,
                "endpoint_actions": 0,
                "sample_count": SAMPLE_COUNT,
                "warmup_count": WARMUP_COUNT,
                "stages_ms": {
                    "normalization": normalization,
                    "evaluation_including_normalization": evaluation,
                    "detection_persistence": persistence,
                    "alert_creation_and_suppression_lookup": alert_creation,
                    "full_normalize_to_detection_and_alert": full_pipeline_result,
                },
                "interpretation": [
                    "Persistence and alert creation are measured independently with fresh records.",
                    "The full path includes broker envelope validation, rule evaluation, persistence, and alert creation.",
                    "Independent stage timings overlap with object construction and are directional rather than additive.",
                ],
            }
            output_path = Path("artifacts/phase7_canonical_pipeline_profile.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(result, sort_keys=True))
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
