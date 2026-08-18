# Canonical Pipeline Performance Analysis

**Date:** 2026-08-18

## Scope and result

This analysis profiles the controlled **normalize → detect → persist → alert** path using temporary SQLite and non-destructive BAS-style fixtures. It has no external calls, broker I/O, endpoint action, firewall action, Wazuh active response, or production database dependency. The measurements are therefore regression diagnostics for this code path, not production sizing claims.

The benchmark target was a canonical-pipeline **p50 below 7 ms**. Removing two redundant post-commit reads reduced the reproducible benchmark p50 from **7.842 ms** to **5.964 ms**, a measured **23.00%** reduction. Throughput increased from **122.77** to **160.84 events/second**, a measured **31.00%** increase. The target is met for the isolated p50; the p95 remains **8.100 ms** and requires production-database validation before any service objective is claimed.

## Stage-level attribution

The dedicated profiler used 150 measured samples after 20 warm-up events. Independent timings intentionally overlap object construction and are directional rather than additive.

| Pipeline boundary | Baseline p50 | Optimized p50 | Observed interpretation |
|---|---:|---:|---|
| Normalization | 0.014 ms | 0.015 ms | Pydantic envelope construction, serialization, and provenance DNA tagging are not the bottleneck. |
| Evaluation including normalization | 0.023 ms | 0.024 ms | Deterministic BAS rule lookup, matching, MITRE evidence construction, and payload fingerprinting are negligible in this fixture. |
| Durable detection persistence | 4.132 ms | 2.623 ms | Database round trips dominate. |
| Alert creation and suppression lookup | 4.402 ms | 2.603 ms | Suppression lookup plus alert persistence dominates. |
| Full normalize-to-detection-and-alert path | 7.331 ms | 4.647 ms | The profiler shows a **36.00%** p50 reduction after the hot-path change. |

The separately maintained Phase 7 benchmark confirms the same direction at its 120-sample scale:

| Metric | Before | After |
|---|---:|---:|
| Pipeline p50 | 7.842 ms | 5.964 ms |
| Pipeline p95 | 10.367 ms | 8.100 ms |
| Pipeline p99 | 10.917 ms | 9.650 ms |
| Pipeline throughput | 122.77 events/s | 160.84 events/s |

## Bottleneck and applied optimization

Before this change, a newly matched event incurred three database interactions for detection evidence and three for the analyst alert. Detection persistence performed an idempotency lookup, commit, and `refresh`; alert creation performed a suppression lookup, commit, and `refresh`. In this SQLite benchmark, the two post-commit refreshes accounted for approximately half of the measured persistence-stage latency.

The processor now omits post-commit `refresh` calls only in canonical detection persistence and alert ingestion. This preserves the durability and governance boundary: both records still commit before a result is returned; the detection repository retains its idempotency lookup, database uniqueness constraint, and conflict fallback; the alert workflow retains tenant-scoped suppression lookup and lifecycle rules. The returned contracts expose only explicitly supplied governed fields, and the session factory uses `expire_on_commit=False`, so the refreshes supplied no contract-relevant data.

> The change intentionally does **not** batch, defer, or weaken durable detection or alert creation. It removes redundant reads after the write is already committed.

## Remaining latency constraints

The p95 and p99 still reflect two independent durable write transactions per new detection: one for detection evidence and one for analyst alert state. The next production-focused opportunities should be evaluated only against PostgreSQL with representative concurrency and retention volumes.

| Opportunity | Expected benefit | Required guardrails |
|---|---|---|
| Add a composite index aligned with active-alert suppression lookup: tenant, suppression key, status, and recent last-seen ordering/filtering | Reduces query cost as alert history grows beyond the small SQLite fixture. | Add a reviewed Alembic migration; verify PostgreSQL query plans and preserve tenant predicate. |
| Use database-native conflict-aware insert for the detection happy path | Can remove the pre-insert duplicate lookup for new deliveries. | Preserve at-least-once semantics across both `detection_id` and tenant/event/rule uniqueness; retain deterministic duplicate retrieval and add concurrency tests. |
| Make detection evidence and alert creation a deliberately designed atomic unit or durable outbox flow | Could reduce commits or move non-critical fan-out from the latency budget. | Do not allow a detection to exist without governed alert recovery, or an alert without detection evidence; retain replay safety and auditability. |
| Tune production connection pools, PostgreSQL indexes, WAL/checkpoint policy, and storage IOPS | Targets tail latency rather than local CPU cost. | Benchmark under controlled load on the target deployment class; do not extrapolate from SQLite. |

The raw latest benchmark is stored in `artifacts/phase7_canonical_soc_benchmark.json`, while the reproducible stage profiler is `scripts/profile_canonical_pipeline.py`.
