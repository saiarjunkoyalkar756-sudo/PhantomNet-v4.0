# Governed Correlation Engineering

## Purpose

The governed correlation engine adds tenant-owned, deterministic detection rules to PhantomNet’s canonical ingestion path. It replaces unsafe free-form matching with structured predicates over canonical event fields and retains bounded match evidence before a threshold becomes a detection.

> **Detection and correlation are advisory.** A governed rule can create durable detection and alert evidence, but it cannot contain an endpoint, modify a cloud firewall, execute a playbook, or invoke any response adapter.

## Rule boundary

A governed rule has a tenant UUID, numeric dotted version, bounded event types, structured predicates, MITRE techniques and tactics, an optional correlation key, a threshold, and a time window. The contract rejects undeclared fields, raw query text, response-action properties, unsafe field paths, nested arbitrary values, and invalid MITRE IDs.

| Rule element | Allowed form | Safety property |
|---|---|---|
| Field path | Bounded canonical dot path such as `payload.hostname` | No raw database, graph, or query expression |
| Operators | `equals`, `contains`, `gte`, `lte`, `in` | Deterministic and testable evaluation |
| Values | Scalar or bounded scalar list | No arbitrary executable or nested object payload |
| Threshold | 1–100 matches | Bounded correlation state |
| Window | 1 second–24 hours | Bounded temporal lookback |
| MITRE evidence | Valid `T####` or `T####.###` IDs | Analyst-readable technique coverage |

## Correlation evidence

Every matching event receives an idempotent durable match receipt keyed by tenant, rule, and event. The engine computes a hash-based correlation key from the declared key fields; when none are declared, it falls back to the canonical event correlation ID or source/event-type grouping. It counts matching receipts within the governed window and emits a detection only when the configured threshold is met.

Duplicate broker delivery reads the existing receipt. It neither creates a second match nor changes the threshold count. When the same detection reaches the alert workflow again, the workflow recognizes it as an already-linked transport duplicate and leaves the analyst alert occurrence count unchanged.

## Analyst APIs

| Route | Required capability | Behavior |
|---|---|---|
| `GET /governed-rules` | `alerts:read` | Lists only rules owned by the authenticated tenant |
| `POST /governed-rules` | `rules:write` | Creates or updates a structured tenant-owned rule after tenant-scope validation |
| `GET /governed-rules/quality` | `alerts:read` | Returns tenant-owned match counts, detection counts, and last-match time without automatic tuning |

## Quality telemetry

Rule quality output contains only non-sensitive operational evidence: rule identity, enabled state, severity, matching-event count, threshold-detection count, and normalized UTC last-match time. It does not claim precision, recall, or false-positive rates without analyst-labeled ground truth.

## Deployment and validation

The migration `b4e8c1d6f2a9_add_governed_correlation.py` creates tenant-scoped governed-rule and match-evidence tables. Isolated tests cover contract rejection, tenant isolation, persistence before threshold, MITRE detection after threshold, idempotent upsert, canonical broker integration, replay-safe alert handling, and API route wiring. Full broker deployment validation remains a Docker-capable-host task because this sandbox has no Redpanda deployment.
