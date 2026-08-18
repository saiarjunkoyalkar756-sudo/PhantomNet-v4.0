# Phase 7 — Controlled Integration and Benchmark Evidence

**Date:** 2026-08-18
**Scope:** Canonical SOC workflow validation in an isolated SQLite sandbox with simulated adapters only.

## Verified workflow

The controlled end-to-end test exercised the following sequence without Kafka, external APIs, endpoint agents, firewall commands, or a production database:

1. Safe BAS telemetry was normalized into the shared canonical event envelope.
2. The canonical processor persisted governed detections and created analyst alerts.
3. An alert was linked to an investigation case and progressed through a non-dispatching case playbook lifecycle.
4. A registered Wazuh-compatible forwarder streamed a replay-protected integrity-alert batch into endpoint asset and integrity evidence storage.
5. A human-approved containment request used an in-process simulated adapter to produce verified execution and rollback evidence.
6. The four containment lifecycle audit records were HMAC-signed and successfully verified as a chain.

> No external containment or remediation action was performed. The simulated adapter records only in-process method calls and has no command, network, firewall, Wazuh active-response, or endpoint-agent capability.

## Benchmark result

The reproducible benchmark harness is `scripts/benchmark_canonical_soc.py`. It uses 120 safe, independently correlated BAS-style events and one 25-alert Wazuh-compatible batch.

| Boundary | Result |
|---|---:|
| Canonical normalize → detect → alert samples | 120 |
| Canonical pipeline throughput | 122.77 events/second |
| Canonical pipeline p50 latency | 7.842 ms |
| Canonical pipeline p95 latency | 10.367 ms |
| Canonical pipeline p99 latency | 10.917 ms |
| Canonical pipeline maximum latency | 12.102 ms |
| Wazuh-compatible 25-alert batch latency | 233.427 ms |
| Wazuh canonical events emitted | 50 |
| Wazuh integrity observations created | 25 |
| Simulated approved containment plus rollback | 20.848 ms |
| Containment audit records | 4 |
| Signed audit chain verification | Passed |

The raw, non-sensitive result is retained in `artifacts/phase7_canonical_soc_benchmark.json`.

## Regression and build validation

| Validation | Result |
|---|---|
| Full Python suite | 158 passed, 0 failed, 0 errors, 0 warnings |
| Dashboard production build | Passed cleanly |
| Docker availability in this sandbox | Unavailable |

## Interpretation and limits

These measurements are useful as **regression evidence for the isolated canonical code path**, not as production capacity, hardware-sizing, or service-level claims. The benchmark uses temporary SQLite and simulated adapters; it does not exercise PostgreSQL, Redpanda/Kafka, Redis, Neo4j, Docker Compose, live Wazuh agents, external response providers, or persistent endpoint control.

A Docker-capable environment is required to validate `docker-compose.integration.yml`, broker consumer groups, actual dependency health gates, multi-container resource behavior, and the true end-to-end latency of the deployed platform.
